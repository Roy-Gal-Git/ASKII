"""Base class for Strands agent wrappers.

These classes are thin wrappers that *create* configured `strands.Agent` instances.
"""

import abc
import os
from typing import Any

from pydantic import BaseModel
from strands import Agent  # type: ignore[import-not-found]


class Base(abc.ABC):
    """Abstract base class for Strands agent wrappers."""

    @staticmethod
    def _set_tool_consent_bypass() -> None:
        """Ensure Strands tools can run non-interactively in CLI flows."""

        os.environ.setdefault("BYPASS_TOOL_CONSENT", "true")

    # ---- Required template methods ----

    @abc.abstractmethod
    def _system_prompt(self) -> str:
        """Define persona and high-level guidelines for the agent."""

    @abc.abstractmethod
    def _model(self) -> Any:
        """Return the configured model instance (e.g. GeminiModel(...))."""

    @abc.abstractmethod
    def _name(self) -> str:
        """Return the agent name."""

    # ---- Optional template methods ----

    def _tools(self) -> list[Any]:
        """Return Strands tool list (default: no tools)."""

        return []

    def _tool_executor(self) -> Any | None:
        """Return the tool executor (default: None)."""

        return None

    def _callback_handler(self) -> Any | None:
        """Return callback handler (default: None)."""

        return None

    def _structured_output_model(self) -> type[BaseModel] | None:
        """Return Pydantic model for structured output (default: None)."""

        return None

    # ---- Public API ----

    def create(self) -> "Agent":
        """Create a new Strands Agent instance."""

        self._set_tool_consent_bypass()
        return Agent(
            model=self._model(),
            name=self._name(),
            system_prompt=self._system_prompt(),
            tools=self._tools(),
            tool_executor=self._tool_executor(),
            callback_handler=self._callback_handler(),
            structured_output_model=self._structured_output_model(),
        )
