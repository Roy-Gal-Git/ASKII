"""Tests for chunking strategies and utilities."""

import tempfile
from pathlib import Path

import pytest

from src.chunking.ast_chunker import chunk_python_file
from src.chunking.chunker import chunk_file, chunk_file_from_path
from src.chunking.sliding_window import chunk_text_file
from src.chunking.token_counter import (
    count_tokens,
    decode_tokens,
    split_text_to_tokens,
    validate_chunk_size,
)


# ============================================================================
# Token Counter Tests
# ============================================================================


def test_count_tokens_basic():
    """Test basic token counting."""
    text = "Hello world"
    count = count_tokens(text)
    assert count > 0
    assert isinstance(count, int)


def test_count_tokens_empty_string():
    """Test token counting with empty string."""
    assert count_tokens("") == 0


def test_count_tokens_multiline():
    """Test token counting with multiline text."""
    text = "Line 1\nLine 2\nLine 3"
    count = count_tokens(text)
    assert count > 0


def test_validate_chunk_size_within_limit():
    """Test validate_chunk_size with text within limit."""
    text = "Short text"
    assert validate_chunk_size(text, max_tokens=100) is True


def test_validate_chunk_size_exceeds_limit():
    """Test validate_chunk_size with text exceeding limit."""
    # Create text that exceeds 10 tokens
    text = "This is a very long text that should exceed ten tokens easily"
    assert validate_chunk_size(text, max_tokens=10) is False


def test_split_text_to_tokens():
    """Test splitting text into token IDs."""
    text = "Hello world"
    tokens = split_text_to_tokens(text)
    assert isinstance(tokens, list)
    assert all(isinstance(t, int) for t in tokens)
    assert len(tokens) > 0


def test_decode_tokens_round_trip():
    """Test that encoding and decoding tokens preserves text."""
    original_text = "Hello world"
    tokens = split_text_to_tokens(original_text)
    decoded = decode_tokens(tokens)
    assert decoded == original_text


# ============================================================================
# AST Chunker Tests
# ============================================================================


def test_chunk_python_file_simple_function():
    """Test AST chunker extracts simple function."""
    source = """
def hello():
    return "world"
"""
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.py"
    chunks = chunk_python_file(file_path, source, repo_path)

    assert len(chunks) == 1
    assert chunks[0].symbol_name == "hello"
    assert chunks[0].symbol_type == "function"
    assert "def hello()" in chunks[0].text
    assert chunks[0].file_path == "test.py"


def test_chunk_python_file_class():
    """Test AST chunker extracts class."""
    source = """
class MyClass:
    def method(self):
        pass
"""
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.py"
    chunks = chunk_python_file(file_path, source, repo_path)

    assert len(chunks) >= 1
    class_chunks = [c for c in chunks if c.symbol_type == "class"]
    assert len(class_chunks) == 1
    assert class_chunks[0].symbol_name == "MyClass"


def test_chunk_python_file_with_decorator():
    """Test AST chunker includes decorators."""
    source = """
@property
def get_value():
    return 42
"""
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.py"
    chunks = chunk_python_file(file_path, source, repo_path)

    assert len(chunks) == 1
    assert "@property" in chunks[0].text
    assert chunks[0].symbol_name == "get_value"


def test_chunk_python_file_async_function():
    """Test AST chunker handles async functions."""
    source = """
async def fetch_data():
    return await some_api()
"""
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.py"
    chunks = chunk_python_file(file_path, source, repo_path)

    assert len(chunks) == 1
    assert chunks[0].symbol_name == "fetch_data"
    assert chunks[0].symbol_type == "function"
    assert "async def" in chunks[0].text


def test_chunk_python_file_nested_definitions():
    """Test AST chunker handles nested definitions."""
    source = """
class Outer:
    def outer_method(self):
        def inner_function():
            return "inner"
        return inner_function()
"""
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.py"
    chunks = chunk_python_file(file_path, source, repo_path)

    # Should extract both class and nested function
    assert len(chunks) >= 2
    symbol_names = {c.symbol_name for c in chunks}
    assert "Outer" in symbol_names
    assert "inner_function" in symbol_names


def test_chunk_python_file_syntax_error():
    """Test AST chunker handles syntax errors gracefully."""
    source = """
def broken_function(
    # Missing closing parenthesis
"""
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.py"
    chunks = chunk_python_file(file_path, source, repo_path)

    # Should return empty list on syntax error
    assert chunks == []


def test_chunk_python_file_empty_file():
    """Test AST chunker handles empty file."""
    source = ""
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.py"
    chunks = chunk_python_file(file_path, source, repo_path)

    assert chunks == []


def test_chunk_python_file_line_ranges():
    """Test AST chunker calculates line ranges correctly."""
    source = """
def func1():
    pass

def func2():
    pass
"""
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.py"
    chunks = chunk_python_file(file_path, source, repo_path)

    assert len(chunks) == 2
    # Check that line ranges are in correct format
    for chunk in chunks:
        assert "-" in chunk.line_range
        start, end = map(int, chunk.line_range.split("-"))
        assert start <= end


# ============================================================================
# Sliding Window Chunker Tests
# ============================================================================


def test_chunk_text_file_empty():
    """Test sliding window chunker handles empty file."""
    source = ""
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.txt"
    chunks = chunk_text_file(file_path, source, repo_path)

    assert chunks == []


def test_chunk_text_file_smaller_than_chunk_size():
    """Test sliding window creates single chunk for small files."""
    source = "Short text"
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.txt"
    chunks = chunk_text_file(file_path, source, repo_path, chunk_size=300)

    assert len(chunks) == 1
    assert chunks[0].text == source


def test_chunk_text_file_with_overlap():
    """Test sliding window creates overlapping chunks."""
    # Create text that will require multiple chunks
    source = " ".join(["word"] * 500)  # Large text
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.txt"
    chunks = chunk_text_file(file_path, source, repo_path, chunk_size=50, overlap_percent=0.2)

    assert len(chunks) > 1
    # Check that chunks have overlap (some text should appear in consecutive chunks)
    if len(chunks) >= 2:
        chunk1_end = chunks[0].text[-50:]
        chunk2_start = chunks[1].text[:50]
        # There should be some overlap
        assert len(set(chunk1_end.split()) & set(chunk2_start.split())) > 0


def test_chunk_text_file_line_ranges():
    """Test sliding window estimates line ranges."""
    source = "Line 1\nLine 2\nLine 3\nLine 4"
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.txt"
    chunks = chunk_text_file(file_path, source, repo_path, chunk_size=10)

    for chunk in chunks:
        assert "-" in chunk.line_range
        start, end = map(int, chunk.line_range.split("-"))
        assert start >= 1
        assert end >= start


def test_chunk_text_file_token_count():
    """Test sliding window chunks have correct token counts."""
    source = " ".join(["word"] * 100)
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.txt"
    chunks = chunk_text_file(file_path, source, repo_path, chunk_size=50)

    for chunk in chunks:
        assert chunk.token_count > 0
        assert chunk.token_count <= 50  # Should respect chunk_size


# ============================================================================
# Chunker Router Tests
# ============================================================================


def test_chunk_file_routes_python_to_ast():
    """Test chunk_file routes .py files to AST chunker."""
    source = """
def test_func():
    return True
"""
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.py"
    chunks = chunk_file(file_path, source, repo_path)

    # AST chunker should extract the function
    assert len(chunks) == 1
    assert chunks[0].symbol_name == "test_func"
    assert chunks[0].symbol_type == "function"


def test_chunk_file_routes_non_python_to_sliding_window():
    """Test chunk_file routes non-Python files to sliding window."""
    source = "This is a text file with some content."
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/test.txt"
    chunks = chunk_file(file_path, source, repo_path)

    # Sliding window should create chunks (may be single chunk if small)
    assert len(chunks) >= 1
    # Non-Python chunks shouldn't have symbol names
    assert chunks[0].symbol_name is None


def test_chunk_file_from_path_reads_file():
    """Test chunk_file_from_path reads and chunks file from disk."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = temp_dir
        file_path = Path(temp_dir) / "test.py"
        file_path.write_text('def hello():\n    return "world"\n')

        chunks = chunk_file_from_path(str(file_path), repo_path)

        assert len(chunks) == 1
        assert chunks[0].symbol_name == "hello"


def test_chunk_file_from_path_nonexistent_file():
    """Test chunk_file_from_path raises IOError for nonexistent file."""
    repo_path = "/tmp/repo"
    file_path = "/tmp/repo/nonexistent.py"

    with pytest.raises(IOError):
        chunk_file_from_path(file_path, repo_path)


def test_chunk_file_from_path_handles_encoding_errors():
    """Test chunk_file_from_path handles encoding errors gracefully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = temp_dir
        file_path = Path(temp_dir) / "test.py"
        # Write binary data that's not valid UTF-8
        file_path.write_bytes(b"\xff\xfe\x00\x01")

        # Should not raise, but may return empty chunks or handle gracefully
        chunks = chunk_file_from_path(str(file_path), repo_path)
        # The function uses errors="ignore", so it should return something
        assert isinstance(chunks, list)

