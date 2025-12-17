"""Indexer node (deterministic MultiAgentBase) for targeted indexing.

This node consumes Explorer's structured output: a Pydantic model in
`AgentResult.structured_output` containing `files: list[str]` of absolute file
paths.

It performs best-effort indexing: it will skip invalid/unreadable paths and
continue indexing the rest.

Strict contract: If the incoming task does not provide a Pydantic structured
output with `.files`, the node raises a clear error (so upstream wiring is fixed
explicitly rather than adding speculative compatibility logic).
"""

import os
from dataclasses import dataclass
from typing import Any

from chromadb import Collection

from src.chunking.chunker import chunk_file_from_path
from src.chunking.models import Chunk

from strands.agent.agent_result import AgentResult
from strands.multiagent.base import MultiAgentBase, MultiAgentResult, NodeResult, Status
from strands.types.content import Message


def _add_chunks_to_collection(collection: Collection, chunks: list[Chunk]) -> None:
    if not chunks:
        return

    documents = [chunk.text for chunk in chunks]
    ids = [chunk.chunk_id for chunk in chunks]
    metadatas = [
        {
            "file_path": chunk.file_path,
            "line_range": chunk.line_range,
            "symbol_name": chunk.symbol_name or "",
            "symbol_type": chunk.symbol_type or "",
            "token_count": chunk.token_count,
        }
        for chunk in chunks
    ]

    collection.add(documents=documents, metadatas=metadatas, ids=ids)


def _delete_chunks_by_file_path(
    collection: Collection, file_paths: list[str], repo_path: str
) -> int:
    if not file_paths:
        return 0

    repo_path_abs = os.path.abspath(repo_path)

    normalized_paths = set()
    for file_path in file_paths:
        if os.path.isabs(file_path):
            try:
                rel_path = os.path.relpath(file_path, repo_path_abs)
                normalized_paths.add(rel_path)
            except ValueError:
                normalized_paths.add(file_path)
        else:
            normalized_paths.add(file_path)

    deleted_count = 0

    try:
        all_results = collection.get()
        if not all_results or not all_results.get("ids"):
            return 0

        ids_to_delete: list[str] = []
        if all_results.get("metadatas"):
            for i, metadata in enumerate(all_results["metadatas"]):
                if not metadata:
                    continue
                chunk_file_path = metadata.get("file_path", "")
                if not chunk_file_path:
                    continue

                for target_path in normalized_paths:
                    if chunk_file_path == target_path:
                        ids_to_delete.append(all_results["ids"][i])
                        break
                    if chunk_file_path.endswith(target_path) or target_path in chunk_file_path:
                        ids_to_delete.append(all_results["ids"][i])
                        break

        if ids_to_delete:
            batch_size = 100
            for i in range(0, len(ids_to_delete), batch_size):
                batch = ids_to_delete[i : i + batch_size]
                try:
                    collection.delete(ids=batch)
                    deleted_count += len(batch)
                except Exception as e:
                    import warnings

                    warnings.warn(f"Failed to delete batch of chunks: {str(e)}")

    except Exception as e:
        import warnings

        warnings.warn(f"Failed to delete chunks for files {file_paths}: {str(e)}")

    return deleted_count


def _extract_files_abs(task: Any) -> list[str]:
    """Extract absolute file paths from Explorer structured output.

    Expected input shape:
    - task is an `AgentResult`
    - task.structured_output is a Pydantic model with `.files: list[str]`

    Raises:
        TypeError: if the expected structured output is not present.
    """
    structured_output = getattr(task, "structured_output", None)
    if structured_output is None:
        raise TypeError(
            "IndexerNode expected task to be a Strands AgentResult with structured_output. "
            f"Got type={type(task)!r}"
        )

    files = getattr(structured_output, "files", None)
    if not isinstance(files, list) or not all(isinstance(p, str) for p in files):
        raise TypeError(
            "IndexerNode expected structured_output.files to be a list[str] of absolute paths. "
            f"Got structured_output={type(structured_output)!r} files_type={type(files)!r}"
        )

    return files


def _run_indexing(
    *,
    files_abs: list[str],
    repo_path: str,
    collection: Collection,
    already_indexed: set[str],
) -> "IndexingRun":
    """Index a list of absolute file paths into ChromaDB.

    This runner is deterministic and best-effort: it attempts each file and
    continues on errors.
    """
    repo_abs = os.path.abspath(str(repo_path))

    indexed_abs: list[str] = []
    indexed_rel: list[str] = []
    skipped_abs: list[str] = []
    errors: list[str] = []

    for raw_path in files_abs:
        abs_path = os.path.abspath(str(raw_path).strip())

        if not abs_path or not os.path.isfile(abs_path):
            skipped_abs.append(abs_path)
            continue

        # Ensure we never index files outside the target repository.
        try:
            in_repo = os.path.commonpath([repo_abs, abs_path]) == repo_abs
        except Exception:
            in_repo = False
        if not in_repo:
            skipped_abs.append(abs_path)
            continue

        rel_path = os.path.relpath(abs_path, repo_abs)
        if rel_path in already_indexed:
            skipped_abs.append(abs_path)
            continue

        try:
            # Re-index single file deterministically (delete old chunks then add new).
            _delete_chunks_by_file_path(collection, [rel_path], repo_path=repo_abs)
            chunks = chunk_file_from_path(abs_path, repo_path=repo_abs)
            _add_chunks_to_collection(collection, chunks)

            already_indexed.add(rel_path)
            indexed_abs.append(abs_path)
            indexed_rel.append(rel_path)
        except Exception as e:
            errors.append(f"Failed to index {abs_path}: {str(e)}")
            skipped_abs.append(abs_path)
            continue

    return IndexingRun(
        requested_abs=files_abs,
        indexed_abs=indexed_abs,
        indexed_rel=indexed_rel,
        skipped_abs=skipped_abs,
        errors=errors,
    )


@dataclass
class IndexingRun:
    requested_abs: list[str]
    indexed_abs: list[str]
    indexed_rel: list[str]
    skipped_abs: list[str]
    errors: list[str]


class IndexerNode(MultiAgentBase):
    """Deterministic node that indexes Explorer-selected files into Chroma."""

    id = "indexer"
    ACTION = "Indexing relevant files"

    async def invoke_async(  # type: ignore[override]
        self, task: Any, invocation_state: dict[str, Any] | None = None, **kwargs: Any
    ) -> MultiAgentResult:
        if invocation_state is None:
            invocation_state = {}

        repo_path: str = invocation_state["repo_path"]
        collection: Collection = invocation_state["collection"]
        already_indexed: set[str] = invocation_state.setdefault("already_indexed", set())

        files_abs = invocation_state.get("explorer_files_abs")
        if not isinstance(files_abs, list) or not all(isinstance(p, str) for p in files_abs):
            files_abs = _extract_files_abs(task)

        run = _run_indexing(
            files_abs=files_abs,
            repo_path=repo_path,
            collection=collection,
            already_indexed=already_indexed,
        )

        message: Message = {
            "role": "assistant",
            "content": [{"text": f"Indexed {len(run.indexed_rel)} file(s)."}],
        }  # type: ignore[typeddict-item]
        ar = AgentResult(
            stop_reason="end_turn",
            message=message,
            metrics=None,
            state={
                "requested": len(run.requested_abs),
                "indexed": len(run.indexed_rel),
                "skipped": len(run.skipped_abs),
                "errors": run.errors,
            },
            interrupts=None,
            structured_output=None,
        )

        nr = NodeResult(result=ar, execution_time=0, status=Status.COMPLETED)
        return MultiAgentResult(
            status=Status.COMPLETED,
            results={self.id: nr},
            execution_count=1,
            execution_time=0,
        )

    def serialize_state(self) -> dict[str, Any]:
        return {}

    def deserialize_state(self, payload: dict[str, Any]) -> None:
        return
