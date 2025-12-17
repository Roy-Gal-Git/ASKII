"""Explorer agent (rg-only)."""

import os
from typing import Any

from pydantic import BaseModel, Field

from .base import Base

from strands.models.gemini import GeminiModel
from strands_tools import shell


class FilesResponse(BaseModel):
    files: list[str] = Field(..., description="Absolute file paths")


class Explorer(Base):
    """Strands Explorer agent that returns a minimal relevant file list."""

    NAME = "explorer"
    DEFAULT_MODEL_ID = "gemini-2.5-flash"
    DEFAULT_TEMPERATURE = 0.1

    def __init__(self, repo_path: str) -> None:
        if not repo_path or not str(repo_path).strip():
            raise ValueError("repo_path is required")
        self._repo_path = os.path.abspath(str(repo_path))

    def _name(self) -> str:
        return self.NAME

    def _system_prompt(self) -> str:
        return (
            "You are a codebase navigation assistant.\n\n"
            "Goal:\n"
            "Given a repository root and a user question, return a list of relevant files.\n\n"
            f"Repository root (fixed): {self._repo_path}\n\n"
            "Rules:\n"
            "- **CRITICAL**: NEVER edit, create, delete, move, or rename files.\n"
            "- DO NOT read file contents.\n"
            "- Use ripgrep (rg) via the shell tool to locate relevant files.\n"
            "- Prefer `rg -l` to return file paths only.\n"
            "- To ensure ABSOLUTE paths, pass the absolute repository root as the PATH argument to rg.\n"
            f"  Example: rg -l -S \"<pattern>\" \"{self._repo_path}\"\n"
            "- You MAY read the textual output produced by `rg` to decide whether a file is relevant.\n"
            "- If you need more signal, you MAY ask `rg` for surrounding context lines around matches (e.g. `rg -n -S -C 3 \"<pattern>\" \"<repo_root>\"`).\n"
            "- Do NOT use other commands to read files (e.g. cat/less/sed/awk/python). Only use `rg`.\n"
            "- Always set the shell tool work_dir to the repository root shown above.\n"
            "- Return at most 10 files.\n"
            "- Output file paths MUST be absolute paths.\n\n"
            "Termination:\n"
            "- Try 2-3 different search patterns maximum. If you find relevant files, return them immediately.\n"
            "- If your searches return no results or only irrelevant files after 2-3 attempts, return an empty list rather than continuing to search.\n"
            "- Do NOT keep trying indefinitely. It's better to return an empty list than to waste time on fruitless searches.\n"
        )

    def _model(self) -> Any:
        return GeminiModel(
            model_id=self.DEFAULT_MODEL_ID,
            params={"temperature": self.DEFAULT_TEMPERATURE},
        )

    def _tools(self) -> list[Any]:
        return [shell]

    def _structured_output_model(self) -> type[BaseModel] | None:
        return FilesResponse
