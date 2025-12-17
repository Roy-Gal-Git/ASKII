"""Error-path tests for CLI-facing validation."""

import tempfile
from pathlib import Path

import pytest

from src.agents.nodes.indexer import _extract_files_abs
from src.agents.nodes.retriever import _parse_line_range
from src.chunking.chunker import chunk_file_from_path
from src.utils.git_utils import get_repo_info


def test_invalid_repository_path_non_git_directory() -> None:
    """Non-git repositories should raise a clear ValueError."""
    with tempfile.TemporaryDirectory() as temp_dir:
        non_git_path = Path(temp_dir) / "not_a_repo"
        non_git_path.mkdir()
        try:
            get_repo_info(str(non_git_path))
            assert False, "Expected get_repo_info() to raise ValueError for non-git directory"
        except ValueError as e:
            assert "not a git repository" in str(e).lower()


def test_invalid_repository_path_nonexistent() -> None:
    """Nonexistent paths should raise a clear ValueError."""
    with pytest.raises(ValueError, match="Path does not exist"):
        get_repo_info("/nonexistent/path/that/does/not/exist")


def test_invalid_repository_path_file_instead_of_directory() -> None:
    """File paths should raise a clear ValueError."""
    # Reset singleton to avoid state from other tests
    import src.utils.git_utils
    src.utils.git_utils._git_repo = None

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        with pytest.raises(ValueError, match="not a directory"):
            get_repo_info(tmp_path)
    finally:
        Path(tmp_path).unlink()
        # Reset singleton after test
        src.utils.git_utils._git_repo = None


def test_chunk_file_from_path_nonexistent_file() -> None:
    """chunk_file_from_path should raise IOError for nonexistent files."""
    with pytest.raises(IOError, match="Failed to read file"):
        chunk_file_from_path("/nonexistent/file.py", "/tmp/repo")


def test_parse_line_range_invalid_format() -> None:
    """_parse_line_range should raise ValueError for invalid formats."""
    with pytest.raises(ValueError, match="Invalid line range format"):
        _parse_line_range("invalid")

    with pytest.raises(ValueError, match="Invalid line range format"):
        _parse_line_range("45")

    with pytest.raises(ValueError, match="Invalid line range format"):
        _parse_line_range("45-67-89")


def test_extract_files_abs_missing_structured_output() -> None:
    """_extract_files_abs should raise TypeError for missing structured_output."""
    class FakeAgentResult:
        def __init__(self):
            self.structured_output = None

    task = FakeAgentResult()

    with pytest.raises(TypeError, match="structured_output"):
        _extract_files_abs(task)


def test_extract_files_abs_invalid_files_type() -> None:
    """_extract_files_abs should raise TypeError for invalid files type."""
    class FakeStructuredOutput:
        def __init__(self):
            self.files = "not a list"

    class FakeAgentResult:
        def __init__(self):
            self.structured_output = FakeStructuredOutput()

    task = FakeAgentResult()

    with pytest.raises(TypeError, match="list\\[str\\]"):
        _extract_files_abs(task)
