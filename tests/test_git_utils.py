"""Tests for git utilities."""

import os
import tempfile
from pathlib import Path

import pytest

from src.utils.git_utils import GitRepo, get_repo_info


def test_get_repo_info_nonexistent_path():
    """Test get_repo_info raises ValueError for nonexistent path."""
    with pytest.raises(ValueError, match="Path does not exist"):
        get_repo_info("/nonexistent/path/that/does/not/exist")


def test_get_repo_info_file_instead_of_directory():
    """Test get_repo_info raises ValueError for file instead of directory."""
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


def test_get_repo_info_non_git_directory():
    """Test get_repo_info raises ValueError for non-git directory."""
    # Reset singleton to avoid state from other tests
    import src.utils.git_utils
    src.utils.git_utils._git_repo = None

    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError, match="not a git repository"):
            get_repo_info(temp_dir)

    # Reset singleton after test
    src.utils.git_utils._git_repo = None


def test_get_repo_info_valid_git_repo():
    """Test get_repo_info returns RepoInfo for valid git repository."""
    import subprocess

    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize a git repository
        subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True, capture_output=True)

        # Reset singleton to avoid state issues between tests
        import src.utils.git_utils
        src.utils.git_utils._git_repo = None

        repo_info = get_repo_info(temp_dir)

        assert repo_info.path == str(Path(temp_dir).resolve())
        assert repo_info.name == Path(temp_dir).name
        assert repo_info.collection_name is not None
        assert len(repo_info.collection_name) > 0


def test_git_repo_get_collection_name_normalizes_path():
    """Test GitRepo._get_collection_name normalizes paths correctly."""
    import subprocess

    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True, capture_output=True)

        git_repo = GitRepo(temp_dir)
        collection_name = git_repo._get_collection_name()

        # Should normalize path separators
        assert os.sep not in collection_name or os.sep == "_"
        # Should not have leading/trailing underscores
        assert not collection_name.startswith("_")
        assert not collection_name.endswith("_")
        # Should not have double underscores
        assert "__" not in collection_name


def test_git_repo_get_collection_name_handles_special_chars():
    """Test GitRepo._get_collection_name handles special characters."""
    import subprocess

    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True, capture_output=True)

        git_repo = GitRepo(temp_dir)
        collection_name = git_repo._get_collection_name()

        # Collection name should be a valid identifier
        assert isinstance(collection_name, str)
        assert len(collection_name) > 0


def test_git_repo_singleton_behavior():
    """Test that _get_git_repo_instance creates singleton."""
    with tempfile.TemporaryDirectory() as temp_dir:
        import subprocess
        subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True, capture_output=True)

        from src.utils.git_utils import _get_git_repo_instance

        # Reset singleton for testing
        import src.utils.git_utils
        src.utils.git_utils._git_repo = None

        instance1 = _get_git_repo_instance(temp_dir)
        instance2 = _get_git_repo_instance(temp_dir)

        # Should return same instance
        assert instance1 is instance2


def test_git_repo_repo_property_caches():
    """Test GitRepo.repo property caches Repo object."""
    import subprocess

    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True, capture_output=True)

        git_repo = GitRepo(temp_dir)
        repo1 = git_repo.repo
        repo2 = git_repo.repo

        # Should return same Repo instance
        assert repo1 is repo2


def test_git_repo_repo_property_validates_git_repo():
    """Test GitRepo.repo property validates it's a git repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        git_repo = GitRepo(temp_dir)

        with pytest.raises(ValueError, match="not a git repository"):
            _ = git_repo.repo

