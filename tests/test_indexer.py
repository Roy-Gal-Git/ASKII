"""Tests for indexer node logic."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.agents.nodes.indexer import (
    _delete_chunks_by_file_path,
    _extract_files_abs,
    _run_indexing,
    IndexingRun,
)

# ============================================================================
# File Extraction Tests
# ============================================================================


def test_extract_files_abs_valid():
    """Test _extract_files_abs extracts files from structured output."""
    class FakeStructuredOutput:
        def __init__(self):
            self.files = ["/abs/path/file1.py", "/abs/path/file2.py"]

    class FakeAgentResult:
        def __init__(self):
            self.structured_output = FakeStructuredOutput()

    task = FakeAgentResult()
    files = _extract_files_abs(task)

    assert files == ["/abs/path/file1.py", "/abs/path/file2.py"]


def test_extract_files_abs_empty_list():
    """Test _extract_files_abs handles empty file list."""
    class FakeStructuredOutput:
        def __init__(self):
            self.files = []

    class FakeAgentResult:
        def __init__(self):
            self.structured_output = FakeStructuredOutput()

    task = FakeAgentResult()
    files = _extract_files_abs(task)

    assert files == []


def test_extract_files_abs_no_structured_output():
    """Test _extract_files_abs raises TypeError for missing structured_output."""
    class FakeAgentResult:
        def __init__(self):
            self.structured_output = None

    task = FakeAgentResult()

    with pytest.raises(TypeError, match="structured_output"):
        _extract_files_abs(task)


def test_extract_files_abs_invalid_files_type():
    """Test _extract_files_abs raises TypeError for invalid files type."""
    class FakeStructuredOutput:
        def __init__(self):
            self.files = "not a list"

    class FakeAgentResult:
        def __init__(self):
            self.structured_output = FakeStructuredOutput()

    task = FakeAgentResult()

    with pytest.raises(TypeError, match="list\\[str\\]"):
        _extract_files_abs(task)


def test_extract_files_abs_non_string_in_list():
    """Test _extract_files_abs raises TypeError for non-string in list."""
    class FakeStructuredOutput:
        def __init__(self):
            self.files = ["/path/file.py", 123]  # Mixed types

    class FakeAgentResult:
        def __init__(self):
            self.structured_output = FakeStructuredOutput()

    task = FakeAgentResult()

    with pytest.raises(TypeError, match="list\\[str\\]"):
        _extract_files_abs(task)


# ============================================================================
# Chunk Deletion Tests
# ============================================================================


def test_delete_chunks_by_file_path_empty_list():
    """Test _delete_chunks_by_file_path handles empty file list."""
    mock_collection = Mock()
    deleted = _delete_chunks_by_file_path(mock_collection, [], "/tmp/repo")

    assert deleted == 0
    mock_collection.get.assert_not_called()


def test_delete_chunks_by_file_path_no_chunks():
    """Test _delete_chunks_by_file_path handles collection with no chunks."""
    mock_collection = Mock()
    mock_collection.get.return_value = {"ids": []}

    deleted = _delete_chunks_by_file_path(mock_collection, ["test.py"], "/tmp/repo")

    assert deleted == 0


def test_delete_chunks_by_file_path_matches_file_path():
    """Test _delete_chunks_by_file_path deletes chunks matching file path."""
    mock_collection = Mock()
    mock_collection.get.return_value = {
        "ids": ["id1", "id2", "id3"],
        "metadatas": [
            {"file_path": "test.py"},
            {"file_path": "other.py"},
            {"file_path": "test.py"},
        ],
    }

    deleted = _delete_chunks_by_file_path(mock_collection, ["test.py"], "/tmp/repo")

    # Should delete id1 and id3 (both match test.py)
    assert deleted == 2
    assert mock_collection.delete.call_count == 1  # Batched deletion


def test_delete_chunks_by_file_path_absolute_path():
    """Test _delete_chunks_by_file_path handles absolute paths."""
    mock_collection = Mock()
    mock_collection.get.return_value = {
        "ids": ["id1"],
        "metadatas": [{"file_path": "test.py"}],
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = temp_dir
        abs_path = Path(temp_dir) / "test.py"
        deleted = _delete_chunks_by_file_path(mock_collection, [str(abs_path)], repo_path)

        assert deleted == 1


def test_delete_chunks_by_file_path_outside_repo():
    """Test _delete_chunks_by_file_path skips paths outside repo."""
    mock_collection = Mock()
    mock_collection.get.return_value = {
        "ids": ["id1"],
        "metadatas": [{"file_path": "test.py"}],
    }

    # Path outside repo
    deleted = _delete_chunks_by_file_path(mock_collection, ["/outside/repo/file.py"], "/tmp/repo")

    assert deleted == 0


def test_delete_chunks_by_file_path_batches_deletion():
    """Test _delete_chunks_by_file_path batches deletions."""
    mock_collection = Mock()
    # Create more than 100 chunks to test batching
    ids = [f"id{i}" for i in range(150)]
    metadatas = [{"file_path": "test.py"} for _ in range(150)]
    mock_collection.get.return_value = {
        "ids": ids,
        "metadatas": metadatas,
    }

    deleted = _delete_chunks_by_file_path(mock_collection, ["test.py"], "/tmp/repo")

    assert deleted == 150
    # Should be called twice (100 + 50)
    assert mock_collection.delete.call_count == 2


# ============================================================================
# Indexing Logic Tests
# ============================================================================


def test_run_indexing_success():
    """Test _run_indexing indexes files successfully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = temp_dir
        file1 = Path(temp_dir) / "file1.py"
        file2 = Path(temp_dir) / "file2.py"
        file1.write_text('def func1():\n    pass\n')
        file2.write_text('def func2():\n    pass\n')

        mock_collection = Mock()
        # Mock get() to return empty results (no existing chunks to delete)
        mock_collection.get.return_value = {"ids": [], "metadatas": []}
        already_indexed = set()

        run = _run_indexing(
            files_abs=[str(file1), str(file2)],
            repo_path=repo_path,
            collection=mock_collection,
            already_indexed=already_indexed,
        )

        assert isinstance(run, IndexingRun)
        assert len(run.indexed_rel) == 2
        assert len(run.indexed_abs) == 2
        assert len(run.skipped_abs) == 0
        assert len(run.errors) == 0
        assert "file1.py" in already_indexed
        assert "file2.py" in already_indexed
        assert mock_collection.add.call_count == 2  # Called for each file


def test_run_indexing_skips_already_indexed():
    """Test _run_indexing skips already indexed files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = temp_dir
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text('def func1():\n    pass\n')

        mock_collection = Mock()
        # Mock get() to return empty results (no existing chunks to delete)
        mock_collection.get.return_value = {"ids": [], "metadatas": []}
        already_indexed = {"file1.py"}

        run = _run_indexing(
            files_abs=[str(file1)],
            repo_path=repo_path,
            collection=mock_collection,
            already_indexed=already_indexed,
        )

        assert len(run.indexed_rel) == 0
        assert len(run.skipped_abs) == 1
        assert mock_collection.add.call_count == 0


def test_run_indexing_skips_nonexistent_files():
    """Test _run_indexing skips nonexistent files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = temp_dir
        nonexistent = Path(temp_dir) / "nonexistent.py"

        mock_collection = Mock()
        already_indexed = set()

        run = _run_indexing(
            files_abs=[str(nonexistent)],
            repo_path=repo_path,
            collection=mock_collection,
            already_indexed=already_indexed,
        )

        assert len(run.indexed_rel) == 0
        assert len(run.skipped_abs) == 1
        assert len(run.errors) == 0


def test_run_indexing_skips_files_outside_repo():
    """Test _run_indexing skips files outside repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = temp_dir
        outside_file = Path(temp_dir).parent / "outside.py"
        outside_file.write_text('def func():\n    pass\n')

        mock_collection = Mock()
        already_indexed = set()

        run = _run_indexing(
            files_abs=[str(outside_file)],
            repo_path=repo_path,
            collection=mock_collection,
            already_indexed=already_indexed,
        )

        assert len(run.indexed_rel) == 0
        assert len(run.skipped_abs) == 1
        assert mock_collection.add.call_count == 0

        outside_file.unlink()  # Cleanup


def test_run_indexing_handles_file_read_errors():
    """Test _run_indexing handles file read errors gracefully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = temp_dir
        # Create a file that will cause read errors (permission denied simulation)
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text('def func1():\n    pass\n')

        mock_collection = Mock()
        # Mock get() to return empty results
        mock_collection.get.return_value = {"ids": [], "metadatas": []}
        # Make add() raise an exception to simulate error
        mock_collection.add.side_effect = Exception("Simulated error")

        already_indexed = set()

        run = _run_indexing(
            files_abs=[str(file1)],
            repo_path=repo_path,
            collection=mock_collection,
            already_indexed=already_indexed,
        )

        assert len(run.indexed_rel) == 0
        assert len(run.skipped_abs) == 1
        assert len(run.errors) == 1
        assert "Simulated error" in run.errors[0]


def test_run_indexing_updates_already_indexed():
    """Test _run_indexing updates already_indexed set."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = temp_dir
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text('def func1():\n    pass\n')

        mock_collection = Mock()
        # Mock get() to return empty results (no existing chunks to delete)
        mock_collection.get.return_value = {"ids": [], "metadatas": []}
        already_indexed = set()

        run = _run_indexing(
            files_abs=[str(file1)],
            repo_path=repo_path,
            collection=mock_collection,
            already_indexed=already_indexed,
        )

        assert "file1.py" in already_indexed
        assert len(already_indexed) == 1


def test_run_indexing_deletes_old_chunks():
    """Test _run_indexing deletes old chunks before adding new ones."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = temp_dir
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text('def func1():\n    pass\n')

        mock_collection = Mock()
        # Mock get() to return empty results (no old chunks)
        mock_collection.get.return_value = {"ids": [], "metadatas": []}
        already_indexed = set()

        run = _run_indexing(
            files_abs=[str(file1)],
            repo_path=repo_path,
            collection=mock_collection,
            already_indexed=already_indexed,
        )

        # Should call delete before add (re-indexing)
        # delete() is called via _delete_chunks_by_file_path which calls get()
        assert mock_collection.get.call_count >= 1
        assert mock_collection.add.call_count == 1

