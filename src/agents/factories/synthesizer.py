"""Synthesizer agent factory (new format).

This is a thin wrapper that creates a configured `strands.Agent`.

Important:
- In graph execution, we do NOT control the user prompt. The graph will pass all
  per-run context (question, retrieved snippets, evidence stats) as the task input.
- Therefore, behavior (format, citations, guardrails, weak/no-evidence handling)
  is primarily enforced via the agent's system prompt.
"""

from typing import Any

from .base import Base

from strands.models.gemini import GeminiModel


class Synthesizer(Base):
    """Strands Synthesizer agent that produces a cited answer from provided context."""

    NAME = "synthesizer"
    ACTION = "Thinking"
    DEFAULT_MODEL_ID = "gemini-2.5-flash"
    DEFAULT_TEMPERATURE = 0.7
    MAX_OUTPUT_TOKENS = 8192

    def _name(self) -> str:
        return self.NAME

    def _system_prompt(self) -> str:
        # NOTE: We intentionally keep this prompt format-agnostic.
        # The graph will provide the per-run context (question/snippets/evidence) in the task input.
        no_evidence_message = (
            "I couldn't find relevant code in the repository to answer this question.\n\n"
            "The repository may not contain code related to your question, or the code "
            "might be indexed under different terms. Try rephrasing your question or "
            "checking if the repository has been fully indexed."
        )

        return (
            "You are a code analyst assistant for answering questions about a repository.\n\n"
            "The user/task input you receive will include the user's question and the relevant "
            "retrieved code snippets (often with file paths and line ranges). The graph runtime "
            "provides all per-run context; do not ask for missing context.\n\n"
            "Rules:\n"
            "- Output MUST be plain text (no markdown).\n"
            "- Every statement about the repository's code MUST be supported by the provided snippets.\n"
            "- Every sentence that makes a code claim MUST include an inline citation in this format: [file.py:start-end].\n"
            "- Use square brackets for citations, not parentheses.\n"
            "- Prefer ONE citation per sentence. If multiple sources are needed, either split sentences or list them together at the end: [a.py:1-2, b.py:3-4].\n"
            "- Do not speculate. If the snippets do not show something, say so.\n"
            "- Never suggest editing/modifying the repository.\n\n"
            "Evidence handling:\n"
            "- If the input contains NO retrieved snippets (or explicitly indicates none), respond EXACTLY with:\n"
            f"{no_evidence_message}\n\n"
            "- If snippets are present but insufficient to answer confidently, hedge explicitly (e.g., 'Based on the available snippets...'), "
            "state what's unclear, and avoid guessing.\n\n"
            "Response requirements:\n"
            "- Be concise and directly answer the question using only the provided snippets.\n"
            "- Do not include preambles like 'Based on the codebase...' unless evidence is weak.\n"
        )

    def _model(self) -> Any:
        return GeminiModel(
            model_id=self.DEFAULT_MODEL_ID,
            params={
                "temperature": self.DEFAULT_TEMPERATURE,
                "max_output_tokens": self.MAX_OUTPUT_TOKENS,
            },
        )

