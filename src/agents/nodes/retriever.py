"""Retriever node (deterministic MultiAgentBase) for retrieval + gating."""
from typing import Any, Tuple

from chromadb import Collection

from src.chunking.models import Chunk, RetrievalResult

from strands.agent.agent_result import AgentResult
from strands.multiagent.base import MultiAgentBase, MultiAgentResult, NodeResult, Status
from strands.types.content import Message


STRONG_THRESHOLD = 0.7
SIMILARITY_THRESHOLD = 0.7
MAX_ATTEMPTS = 3


def _parse_line_range(line_range: str) -> Tuple[int, int]:
    try:
        parts = line_range.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid line range format: {line_range}")
        start = int(parts[0])
        end = int(parts[1])
        return (start, end)
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid line range format: {line_range}") from e


def _chunks_overlap(chunk1: Chunk, chunk2: Chunk) -> bool:
    if chunk1.file_path != chunk2.file_path:
        return False

    try:
        start1, end1 = _parse_line_range(chunk1.line_range)
        start2, end2 = _parse_line_range(chunk2.line_range)
        return start1 <= end2 and start2 <= end1
    except ValueError:
        return False


def _deduplicate_chunks(chunks: list[Chunk]) -> list[Chunk]:
    if not chunks:
        return []

    keep = [True] * len(chunks)
    deduplicated: list[Chunk] = []

    for i, chunk1 in enumerate(chunks):
        if not keep[i]:
            continue

        overlaps_with_kept = False
        for chunk2 in deduplicated:
            if _chunks_overlap(chunk1, chunk2):
                overlaps_with_kept = True
                break

        if not overlaps_with_kept:
            deduplicated.append(chunk1)
            for j in range(i + 1, len(chunks)):
                if keep[j] and _chunks_overlap(chunk1, chunks[j]):
                    keep[j] = False

    return deduplicated


def _distance_to_similarity(distance: float) -> float:
    return max(0.0, min(1.0, 1.0 - distance))


def _retrieve_chunks(collection: Collection, question: str, top_k: int = 10) -> RetrievalResult:
    results = collection.query(query_texts=[question], n_results=top_k)
    ids = results["ids"][0] if results.get("ids") else []
    documents = results["documents"][0] if results.get("documents") else []
    metadatas = results["metadatas"][0] if results.get("metadatas") else []
    distances = results["distances"][0] if results.get("distances") else []

    if not ids or not documents:
        return RetrievalResult(
            chunks=[],
            max_similarity=0.0,
            num_chunks_above_threshold=0,
            distances=[],
        )

    chunks: list[Chunk] = []
    for doc_id, document, metadata in zip(ids, documents, metadatas):
        chunk = Chunk(
            text=document,
            file_path=(metadata or {}).get("file_path", ""),
            line_range=(metadata or {}).get("line_range", "0-0"),
            symbol_name=((metadata or {}).get("symbol_name") or None),
            symbol_type=((metadata or {}).get("symbol_type") or None),
            token_count=(metadata or {}).get("token_count", 0),
            chunk_id=doc_id,
        )
        chunks.append(chunk)

    similarities = [_distance_to_similarity(d) for d in distances]
    max_similarity = max(similarities) if similarities else 0.0
    num_chunks_above_threshold = sum(1 for sim in similarities if sim >= SIMILARITY_THRESHOLD)

    deduplicated_chunks = _deduplicate_chunks(chunks)
    chunk_id_to_distance = {chunk.chunk_id: dist for chunk, dist in zip(chunks, distances)}
    deduplicated_distances = [chunk_id_to_distance[chunk.chunk_id] for chunk in deduplicated_chunks]

    deduplicated_similarities = [_distance_to_similarity(d) for d in deduplicated_distances]
    max_similarity = max(deduplicated_similarities) if deduplicated_similarities else 0.0
    num_chunks_above_threshold = sum(
        1 for sim in deduplicated_similarities if sim >= SIMILARITY_THRESHOLD
    )

    return RetrievalResult(
        chunks=deduplicated_chunks,
        max_similarity=max_similarity,
        num_chunks_above_threshold=num_chunks_above_threshold,
        distances=deduplicated_distances,
    )


class RetrieverNode(MultiAgentBase):
    """Deterministic node that queries Chroma and gates the loop."""

    id = "retriever"
    ACTION = "Retrieving relevant snippets"

    def __init__(self) -> None:
        super().__init__()

    async def invoke_async(  # type: ignore[override]
        self, task: Any, invocation_state: dict[str, Any] | None = None, **kwargs: Any
    ) -> MultiAgentResult:
        if invocation_state is None:
            invocation_state = {}

        question: str = str(invocation_state.get("question") or task)
        collection: Collection = invocation_state["collection"]
        repo_path: str = invocation_state.get("repo_path", "")
        attempts: int = int(invocation_state.get("attempts", 0))

        retrieval_result: RetrievalResult = _retrieve_chunks(collection, question, top_k=10)
        invocation_state["retrieval_result"] = retrieval_result

        max_similarity = float(retrieval_result.max_similarity)
        strong = max_similarity >= STRONG_THRESHOLD and len(retrieval_result.chunks) > 0

        should_synthesize = strong
        if not should_synthesize:
            attempts += 1
            invocation_state["attempts"] = attempts
            should_synthesize = attempts >= MAX_ATTEMPTS

        invocation_state["should_synthesize"] = should_synthesize

        repo_line = f"Repository root: {repo_path}" if repo_path else ""
        text = "\n".join(
            [
                f"Retrieved {len(retrieval_result.chunks)} chunk(s). max_similarity={max_similarity:.4f}.",
                repo_line,
            ]
        ).strip()
        message: Message = {"role": "assistant", "content": [{"text": text}]}  # type: ignore[typeddict-item]
        ar = AgentResult(
            stop_reason="end_turn",
            message=message,
            metrics=None,
            state={
                "approved": should_synthesize,
                "should_synthesize": should_synthesize,
                "attempts": attempts,
                "max_attempts": MAX_ATTEMPTS,
                "max_similarity": max_similarity,
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
