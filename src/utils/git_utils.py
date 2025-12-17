"""Git utilities for repository information extraction."""

import os
from pathlib import Path
from typing import Optional
from git import Repo, InvalidGitRepositoryError
from pydantic import BaseModel


class RepoInfo(BaseModel):
    """Repository information for routing."""

    path: str
    name: str
    collection_name: str


# Module-level singleton GitRepo instance (one repo per application run)
_git_repo: Optional["GitRepo"] = None


def _get_git_repo_instance(path: str) -> "GitRepo":
    """
    Get or create the singleton GitRepo instance.

    Since the application works with a single repository per run,
    this function creates the instance on first call and reuses it.

    Args:
        path: Path to git repository (used only for initialization)

    Returns:
        GitRepo: Singleton instance
    """
    global _git_repo

    if _git_repo is None:
        normalized_path = str(Path(path).expanduser().resolve())
        _git_repo = GitRepo(normalized_path)

    return _git_repo


class GitRepo:
    """
    Git repository wrapper that caches the Repo object for efficiency.

    This class creates a single Repo instance and reuses it for all operations,
    avoiding the overhead of creating multiple Repo objects for the same path.
    """

    def __init__(self, path: str):
        """
        Initialize GitRepo with a path.

        Args:
            path: Path to git repository (should be normalized absolute path)
        """
        # Path should already be normalized when passed from _get_git_repo_instance
        self._path = path
        self._repo: Optional[Repo] = None

    @property
    def repo(self) -> Repo:
        """
        Get the cached Repo object, creating it if necessary.

        Returns:
            Repo: GitPython Repo object

        Raises:
            ValueError: If path is not a git repository
        """
        if self._repo is None:
            try:
                self._repo = Repo(self._path, search_parent_directories=True)
                if self._repo.git_dir is None:
                    raise ValueError(
                        f"Path is not a git repository: {self._path}. "
                        "Please provide a valid git repository path."
                    )
            except InvalidGitRepositoryError as e:
                raise ValueError(
                    f"Path is not a git repository: {self._path}. "
                    "Please provide a valid git repository path."
                ) from e
        return self._repo

    def _get_repo_name(self) -> str:
        """
        Extract repository name from git repository.

        Returns:
            str: Repository name from git working tree

        Raises:
            ValueError: If path is not a git repository
        """
        repo = self.repo
        # Get the working tree directory name
        working_tree = Path(repo.working_tree_dir)
        return working_tree.name

    def _get_collection_name(self) -> str:
        """
        Generate unique collection name from full path.

        Uses normalized absolute path to avoid collisions with duplicate repo names.

        Returns:
            str: Normalized collection name
        """
        abs_path = os.path.abspath(self._path)
        # Normalize path (resolve symlinks, handle ~, etc.)
        normalized = os.path.normpath(abs_path)
        # Replace path separators with underscores for collection name
        # Also replace other special characters
        collection_name = normalized.replace(os.sep, "_")
        # Remove leading/trailing underscores and clean up
        collection_name = collection_name.strip("_")
        # Replace multiple underscores with single underscore
        while "__" in collection_name:
            collection_name = collection_name.replace("__", "_")
        return collection_name

    def get_repo_info(self) -> RepoInfo:
        """
        Get repository information from path.

        Returns:
            RepoInfo: Repository information object

        Raises:
            ValueError: If path does not exist, is not accessible, is not a directory, or is not a git repository
        """
        path_obj = Path(self._path)

        # Validate path exists
        if not path_obj.exists():
            raise ValueError(f"Path does not exist: {self._path}")

        # Validate path is a directory
        if not path_obj.is_dir():
            raise ValueError(f"Path is not a directory: {self._path}")

        # Get all information using cached repo (this will validate it's a git repo)
        repo_name = self._get_repo_name()
        collection_name = self._get_collection_name()

        return RepoInfo(
            path=self._path,
            name=repo_name,
            collection_name=collection_name,
        )


def get_repo_info(path: str) -> RepoInfo:
    """
    Get repository information from path.

    Args:
        path: Path to git repository

    Returns:
        RepoInfo: Repository information object

    Raises:
        ValueError: If path does not exist, is not accessible, or is not a git repository
    """
    git_repo = _get_git_repo_instance(path)
    return git_repo.get_repo_info()
