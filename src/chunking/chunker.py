"""Main chunking interface that routes to appropriate chunking strategy."""

import os
from typing import List
from src.chunking.models import Chunk
from src.chunking.ast_chunker import chunk_python_file
from src.chunking.sliding_window import chunk_text_file


def chunk_file(file_path: str, source: str, repo_path: str) -> List[Chunk]:
    """
    Chunk a file using the appropriate strategy based on file type.

    Args:
        file_path: Absolute path to the file
        source: Source code content of the file
        repo_path: Path to repository root (for relative paths)

    Returns:
        List[Chunk]: List of chunks extracted from the file
    """
    # Determine file extension
    _, ext = os.path.splitext(file_path)
    ext_lower = ext.lower()

    # Use AST chunking for Python files
    if ext_lower == ".py":
        return chunk_python_file(file_path, source, repo_path)
    else:
        # Use sliding window for all other text files
        return chunk_text_file(file_path, source, repo_path)


def chunk_file_from_path(file_path: str, repo_path: str) -> List[Chunk]:
    """
    Chunk a file by reading it from disk.

    Args:
        file_path: Absolute path to the file
        repo_path: Path to repository root (for relative paths)

    Returns:
        List[Chunk]: List of chunks extracted from the file

    Raises:
        IOError: If file cannot be read
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        return chunk_file(file_path, source, repo_path)
    except Exception as e:
        raise IOError(f"Failed to read file {file_path}: {str(e)}") from e
