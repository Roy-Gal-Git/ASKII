"""ExplorerSelect node (bridge): run Explorer Agent and capture selected files.

This node exists because Strands Graph input propagation may pass downstream
nodes a formatted text task rather than the raw upstream `AgentResult`. We
therefore extract Explorer structured output and store it in `invocation_state`.
"""

import io
from contextlib import redirect_stderr, redirect_stdout
from typing import Any

from strands import Agent
from strands.agent.agent_result import AgentResult
from strands.multiagent.base import MultiAgentBase, MultiAgentResult, NodeResult, Status
from strands.types.content import Message
from src.utils.retry import retry_gemini_api


class ExplorerSelectNode(MultiAgentBase):
    """Invoke Explorer agent and persist its file selection to invocation_state."""

    id = "explorer"
    ACTION = "Searching the repository"

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

    def __init__(self, *, agent: Agent) -> None:
        super().__init__()
        self._agent = agent

    @staticmethod
    def _extract_files_abs(explorer_result: AgentResult) -> list[str]:
        structured_output = getattr(explorer_result, "structured_output", None)
        if structured_output is None:
            raise TypeError("ExplorerSelectNode expected Explorer AgentResult.structured_output to be set.")

        files = getattr(structured_output, "files", None)
        if not isinstance(files, list) or not all(isinstance(p, str) for p in files):
            raise TypeError(
                "ExplorerSelectNode expected structured_output.files to be a list[str] of absolute paths. "
                f"Got files_type={type(files)!r}"
            )
        return files

    async def invoke_async(  # type: ignore[override]
        self, task: Any, invocation_state: dict[str, Any] | None = None, **kwargs: Any
    ) -> MultiAgentResult:
        if invocation_state is None:
            invocation_state = {}

        question: str = str(invocation_state.get("question") or task)

        already_indexed = invocation_state.get("already_indexed")
        extra = ""
        if isinstance(already_indexed, set) and already_indexed:
            preview = sorted(list(already_indexed))[:50]
            extra = (
                "\n\nAlready indexed files (avoid repeating these if possible):\n"
                + "\n".join(preview)
            )

        # Tools like `strands_tools.shell` can print to stdout/stderr; keep CLI clean.
        # Wrap agent invocation with retries to handle transient Gemini API errors
        # Increased attempts and delays to handle rate limiting from multiple instances
        @retry_gemini_api(max_attempts=8, base_delay=2.0, max_delay=120.0)
        async def _invoke_agent() -> AgentResult:
            """Invoke the explorer agent with retry logic."""
            return await self._agent.invoke_async(
                f"{question}{extra}",
                invocation_state=invocation_state,
                **kwargs,
            )

        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            explorer_ar: AgentResult = await _invoke_agent()

        files_abs = self._extract_files_abs(explorer_ar)
        invocation_state["explorer_files_abs"] = files_abs

        ar = self._agent_result(
            f"Explorer selected {len(files_abs)} file(s).",
            state={"selected": len(files_abs)},
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

