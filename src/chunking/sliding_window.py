"""Sliding window chunking for non-Python text files."""

import os
from typing import List
from src.chunking.models import Chunk
from src.chunking.token_counter import (
    split_text_to_tokens,
    decode_tokens,
    count_tokens,
)


def chunk_text_file(
    file_path: str,
    source: str,
    repo_path: str,
    chunk_size: int = 300,
    overlap_percent: float = 0.2,
) -> List[Chunk]:
    """
    Chunk a text file using sliding window with overlap.

    Args:
        file_path: Absolute path to the file
        source: Source code content of the file
        repo_path: Path to repository root (for relative paths)
        chunk_size: Target number of tokens per chunk (default: 300)
        overlap_percent: Percentage of overlap between chunks (default: 0.2 = 20%)

    Returns:
        List[Chunk]: List of chunks extracted from the file
    """
    chunks = []

    # Handle edge cases
    if not source or not source.strip():
        # Empty file - return empty list
        return []

    # Tokenize the entire text
    tokens = split_text_to_tokens(source)
    total_tokens = len(tokens)

    # If file is smaller than chunk size, create a single chunk
    if total_tokens <= chunk_size:
        relative_path = os.path.relpath(file_path, repo_path)
        chunk_id = f"{relative_path}:1-{_count_lines(source)}"

        chunk = Chunk(
            text=source,
            file_path=relative_path,
            line_range=f"1-{_count_lines(source)}",
            symbol_name=None,
            symbol_type=None,
            token_count=total_tokens,
            chunk_id=chunk_id,
        )
        return [chunk]

    # Calculate overlap and step size
    overlap_size = int(chunk_size * overlap_percent)
    step_size = chunk_size - overlap_size

    # Split source into lines for line range calculation
    source_lines = source.splitlines(keepends=True)
    total_lines = len(source_lines)

    # Create a mapping from character position to line number
    char_to_line = _create_char_to_line_map(source)

    relative_path = os.path.relpath(file_path, repo_path)

    # Create overlapping chunks
    for i in range(0, total_tokens, step_size):
        chunk_tokens = tokens[i : i + chunk_size]
        if not chunk_tokens:
            break

        # Decode tokens back to text
        chunk_text = decode_tokens(chunk_tokens)

        # Calculate approximate line range for this chunk
        # We approximate by finding where this chunk's text appears in the source
        start_line, end_line = _estimate_line_range(
            chunk_text, source, char_to_line, i, total_tokens
        )

        chunk_id = f"{relative_path}:{start_line}-{end_line}"

        chunk = Chunk(
            text=chunk_text,
            file_path=relative_path,
            line_range=f"{start_line}-{end_line}",
            symbol_name=None,
            symbol_type=None,
            token_count=len(chunk_tokens),
            chunk_id=chunk_id,
        )
        chunks.append(chunk)

        # Stop if we've reached the end
        if i + chunk_size >= total_tokens:
            break

    return chunks


def _count_lines(text: str) -> int:
    """
    Count the number of lines in text.

    Args:
        text: Input text

    Returns:
        int: Number of lines
    """
    if not text:
        return 1
    return len(text.splitlines())


def _create_char_to_line_map(text: str) -> dict:
    """
    Create a mapping from character position to line number.

    Args:
        text: Input text

    Returns:
        dict: Mapping from character index to line number (1-based)
    """
    char_to_line = {}
    line_num = 1
    for i, char in enumerate(text):
        char_to_line[i] = line_num
        if char == "\n":
            line_num += 1
    return char_to_line


def _estimate_line_range(
    chunk_text: str,
    full_text: str,
    char_to_line: dict,
    token_start: int,
    total_tokens: int,
) -> tuple[int, int]:
    """
    Estimate line range for a chunk based on its position in the text.

    Args:
        chunk_text: The chunk text
        char_to_line: Mapping from character position to line number
        token_start: Starting token index of the chunk
        total_tokens: Total number of tokens in the file

    Returns:
        tuple[int, int]: (start_line, end_line) as 1-based line numbers
    """
    # Estimate character position based on token position
    # This is approximate since tokens don't map 1:1 to characters
    estimated_char_start = int((token_start / total_tokens) * len(full_text))
    estimated_char_end = min(
        estimated_char_start + len(chunk_text), len(full_text)
    )

    # Get line numbers from character positions
    start_line = char_to_line.get(estimated_char_start, 1)
    end_line = char_to_line.get(estimated_char_end, start_line)

    # Ensure end_line is at least start_line
    if end_line < start_line:
        end_line = start_line

    # Try to find the chunk text in the source for more accurate line numbers
    chunk_start_in_source = full_text.find(chunk_text[:100])  # Use first 100 chars
    if chunk_start_in_source != -1:
        start_line = char_to_line.get(chunk_start_in_source, start_line)
        chunk_end_in_source = chunk_start_in_source + len(chunk_text)
        end_line = char_to_line.get(
            min(chunk_end_in_source, len(full_text) - 1), end_line
        )

    return (start_line, end_line)
