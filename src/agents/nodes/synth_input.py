"""SynthInput node: format retrieval evidence into a deterministic task for Synthesizer.

The Synthesizer agent relies on the task input to include the user's question
and the retrieved code snippets with file/line citations.
"""

from __future__ import annotations

from typing import Any

from src.chunking.models import RetrievalResult

from strands.agent.agent_result import AgentResult
from strands.multiagent.base import MultiAgentBase, MultiAgentResult, NodeResult, Status
from strands.types.content import Message


class SynthInputNode(MultiAgentBase):
    """Deterministically build a Synthesizer task from invocation_state."""

    id = "synth_input"
    ACTION = "Preparing evidence"

    @staticmethod
    def _agent_result(text: str, state: dict[str, Any]) -> AgentResult:
        message: Message = {"role": "assistant", "content": [{"text": text}]}  # type: ignore[typeddict-item]
        return AgentResult(
            stop_reason="end_turn",
            message=message,
            metrics=None,
            state=state,
            interrupts=None,
            structured_output=None,
        )

    @staticmethod
    def _format_task(*, question: str, retrieval_result: RetrievalResult) -> str:
        chunks = retrieval_result.chunks
        max_similarity = float(retrieval_result.max_similarity)

        parts: list[str] = []
        parts.append("User question:")
        parts.append(question)
        parts.append("")
        parts.append(f"Evidence: {len(chunks)} snippet(s), max_similarity={max_similarity:.4f}")
        parts.append("")
        parts.append("Retrieved snippets (cite as [file_path:start-end]):")

        if not chunks:
            parts.append("No snippets retrieved.")
            return "\n".join(parts).strip() + "\n"

        for i, chunk in enumerate(chunks, 1):
            cite = f"[{chunk.file_path}:{chunk.line_range}]"
            symbol = ""
            if chunk.symbol_name:
                st = chunk.symbol_type or "symbol"
                symbol = f" ({st}: {chunk.symbol_name})"
            parts.append("")
            parts.append(f"Snippet {i}: {cite}{symbol}")
            parts.append("```")
            parts.append(chunk.text.rstrip())
            parts.append("```")

        return "\n".join(parts).strip() + "\n"

    async def invoke_async(  # type: ignore[override]
        self, task: Any, invocation_state: dict[str, Any] | None = None, **kwargs: Any
    ) -> MultiAgentResult:
        if invocation_state is None:
            invocation_state = {}

        question: str = str(invocation_state.get("question") or task)
        retrieval_result: RetrievalResult = invocation_state["retrieval_result"]

        synth_task = self._format_task(question=question, retrieval_result=retrieval_result)
        invocation_state["synth_task"] = synth_task

        ar = self._agent_result(
            synth_task,
            state={
                "snippets": len(retrieval_result.chunks),
                "max_similarity": float(retrieval_result.max_similarity),
            },
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

