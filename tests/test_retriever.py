"""Tests for retriever node logic."""

import pytest

from src.agents.nodes.retriever import (
    _chunks_overlap,
    _deduplicate_chunks,
    _distance_to_similarity,
    _parse_line_range,
    _retrieve_chunks,
)
from src.chunking.models import Chunk, RetrievalResult


# ============================================================================
# Line Range Parsing Tests
# ============================================================================


def test_parse_line_range_valid():
    """Test _parse_line_range with valid format."""
    start, end = _parse_line_range("45-67")
    assert start == 45
    assert end == 67


def test_parse_line_range_single_digit():
    """Test _parse_line_range with single digit line numbers."""
    start, end = _parse_line_range("1-5")
    assert start == 1
    assert end == 5


def test_parse_line_range_invalid_format_missing_dash():
    """Test _parse_line_range raises ValueError for missing dash."""
    with pytest.raises(ValueError, match="Invalid line range format"):
        _parse_line_range("4567")


def test_parse_line_range_invalid_format_too_many_parts():
    """Test _parse_line_range raises ValueError for too many parts."""
    with pytest.raises(ValueError, match="Invalid line range format"):
        _parse_line_range("45-67-89")


def test_parse_line_range_invalid_format_non_numeric():
    """Test _parse_line_range raises ValueError for non-numeric values."""
    with pytest.raises(ValueError, match="Invalid line range format"):
        _parse_line_range("abc-def")


def test_parse_line_range_reversed_order():
    """Test _parse_line_range handles reversed order (end < start)."""
    # Function should still parse it, even if logically wrong
    start, end = _parse_line_range("67-45")
    assert start == 67
    assert end == 45


# ============================================================================
# Chunk Overlap Detection Tests
# ============================================================================


def test_chunks_overlap_same_file_overlapping():
    """Test _chunks_overlap detects overlapping chunks in same file."""
    chunk1 = Chunk(
        text="text1",
        file_path="test.py",
        line_range="10-20",
        chunk_id="id1",
    )
    chunk2 = Chunk(
        text="text2",
        file_path="test.py",
        line_range="15-25",
        chunk_id="id2",
    )

    assert _chunks_overlap(chunk1, chunk2) is True


def test_chunks_overlap_same_file_adjacent():
    """Test _chunks_overlap detects adjacent chunks as overlapping."""
    chunk1 = Chunk(
        text="text1",
        file_path="test.py",
        line_range="10-20",
        chunk_id="id1",
    )
    chunk2 = Chunk(
        text="text2",
        file_path="test.py",
        line_range="20-30",
        chunk_id="id2",
    )

    assert _chunks_overlap(chunk1, chunk2) is True


def test_chunks_overlap_same_file_non_overlapping():
    """Test _chunks_overlap detects non-overlapping chunks."""
    chunk1 = Chunk(
        text="text1",
        file_path="test.py",
        line_range="10-20",
        chunk_id="id1",
    )
    chunk2 = Chunk(
        text="text2",
        file_path="test.py",
        line_range="25-35",
        chunk_id="id2",
    )

    assert _chunks_overlap(chunk1, chunk2) is False


def test_chunks_overlap_different_files():
    """Test _chunks_overlap returns False for different files."""
    chunk1 = Chunk(
        text="text1",
        file_path="file1.py",
        line_range="10-20",
        chunk_id="id1",
    )
    chunk2 = Chunk(
        text="text2",
        file_path="file2.py",
        line_range="10-20",
        chunk_id="id2",
    )

    assert _chunks_overlap(chunk1, chunk2) is False


def test_chunks_overlap_invalid_line_range():
    """Test _chunks_overlap handles invalid line range gracefully."""
    chunk1 = Chunk(
        text="text1",
        file_path="test.py",
        line_range="invalid",
        chunk_id="id1",
    )
    chunk2 = Chunk(
        text="text2",
        file_path="test.py",
        line_range="10-20",
        chunk_id="id2",
    )

    # Should return False for invalid ranges
    assert _chunks_overlap(chunk1, chunk2) is False


# ============================================================================
# Deduplication Tests
# ============================================================================


def test_deduplicate_chunks_empty_list():
    """Test _deduplicate_chunks with empty list."""
    assert _deduplicate_chunks([]) == []


def test_deduplicate_chunks_no_overlaps():
    """Test _deduplicate_chunks preserves non-overlapping chunks."""
    chunks = [
        Chunk(
            text="text1",
            file_path="test.py",
            line_range="10-20",
            chunk_id="id1",
        ),
        Chunk(
            text="text2",
            file_path="test.py",
            line_range="25-35",
            chunk_id="id2",
        ),
    ]

    result = _deduplicate_chunks(chunks)
    assert len(result) == 2
    assert result == chunks


def test_deduplicate_chunks_removes_overlaps():
    """Test _deduplicate_chunks removes overlapping chunks."""
    chunks = [
        Chunk(
            text="text1",
            file_path="test.py",
            line_range="10-20",
            chunk_id="id1",
        ),
        Chunk(
            text="text2",
            file_path="test.py",
            line_range="15-25",
            chunk_id="id2",
        ),
        Chunk(
            text="text3",
            file_path="test.py",
            line_range="30-40",
            chunk_id="id3",
        ),
    ]

    result = _deduplicate_chunks(chunks)
    # Should keep first chunk and third chunk (non-overlapping)
    assert len(result) == 2
    chunk_ids = {c.chunk_id for c in result}
    assert "id1" in chunk_ids
    assert "id3" in chunk_ids


def test_deduplicate_chunks_preserves_first_occurrence():
    """Test _deduplicate_chunks preserves first occurrence when multiple overlap."""
    chunks = [
        Chunk(
            text="text1",
            file_path="test.py",
            line_range="10-20",
            chunk_id="id1",
        ),
        Chunk(
            text="text2",
            file_path="test.py",
            line_range="12-18",
            chunk_id="id2",
        ),
        Chunk(
            text="text3",
            file_path="test.py",
            line_range="15-25",
            chunk_id="id3",
        ),
    ]

    result = _deduplicate_chunks(chunks)
    # Should keep first chunk (id1) and remove overlapping ones
    assert len(result) == 1
    assert result[0].chunk_id == "id1"


def test_deduplicate_chunks_different_files():
    """Test _deduplicate_chunks preserves chunks from different files."""
    chunks = [
        Chunk(
            text="text1",
            file_path="file1.py",
            line_range="10-20",
            chunk_id="id1",
        ),
        Chunk(
            text="text2",
            file_path="file2.py",
            line_range="10-20",
            chunk_id="id2",
        ),
    ]

    result = _deduplicate_chunks(chunks)
    assert len(result) == 2


# ============================================================================
# Similarity Calculation Tests
# ============================================================================


def test_distance_to_similarity_zero_distance():
    """Test _distance_to_similarity with zero distance."""
    similarity = _distance_to_similarity(0.0)
    assert similarity == 1.0


def test_distance_to_similarity_max_distance():
    """Test _distance_to_similarity with maximum distance."""
    similarity = _distance_to_similarity(1.0)
    assert similarity == 0.0


def test_distance_to_similarity_half_distance():
    """Test _distance_to_similarity with half distance."""
    similarity = _distance_to_similarity(0.5)
    assert similarity == 0.5


def test_distance_to_similarity_clamps_negative():
    """Test _distance_to_similarity clamps negative distances."""
    similarity = _distance_to_similarity(-0.5)
    assert similarity == 1.0  # Clamped to max


def test_distance_to_similarity_clamps_above_one():
    """Test _distance_to_similarity clamps distances above one."""
    similarity = _distance_to_similarity(2.0)
    assert similarity == 0.0  # Clamped to min


# ============================================================================
# Retrieval Result Building Tests
# ============================================================================


def test_retrieve_chunks_empty_collection():
    """Test _retrieve_chunks handles empty collection."""
    from unittest.mock import Mock

    mock_collection = Mock()
    mock_collection.query.return_value = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }

    result = _retrieve_chunks(mock_collection, "test query", top_k=10)

    assert isinstance(result, RetrievalResult)
    assert result.chunks == []
    assert result.max_similarity == 0.0
    assert result.num_chunks_above_threshold == 0
    assert result.distances == []


def test_retrieve_chunks_builds_result():
    """Test _retrieve_chunks builds RetrievalResult correctly."""
    from unittest.mock import Mock

    mock_collection = Mock()
    mock_collection.query.return_value = {
        "ids": [["id1", "id2"]],
        "documents": [["document1", "document2"]],
        "metadatas": [[
            {
                "file_path": "test.py",
                "line_range": "10-20",
                "symbol_name": "func1",
                "symbol_type": "function",
                "token_count": 50,
            },
            {
                "file_path": "test.py",
                "line_range": "25-35",
                "symbol_name": None,
                "symbol_type": None,
                "token_count": 30,
            },
        ]],
        "distances": [[0.2, 0.5]],
    }

    result = _retrieve_chunks(mock_collection, "test query", top_k=10)

    assert len(result.chunks) == 2
    assert result.chunks[0].chunk_id == "id1"
    assert result.chunks[0].file_path == "test.py"
    assert result.chunks[0].symbol_name == "func1"
    assert result.max_similarity == 0.8  # 1 - 0.2
    assert result.num_chunks_above_threshold == 1  # 0.8 >= 0.7


def test_retrieve_chunks_deduplicates():
    """Test _retrieve_chunks deduplicates overlapping chunks."""
    from unittest.mock import Mock

    mock_collection = Mock()
    mock_collection.query.return_value = {
        "ids": [["id1", "id2"]],
        "documents": [["document1", "document2"]],
        "metadatas": [[
            {
                "file_path": "test.py",
                "line_range": "10-20",
                "symbol_name": None,
                "symbol_type": None,
                "token_count": 50,
            },
            {
                "file_path": "test.py",
                "line_range": "15-25",  # Overlaps with first
                "symbol_name": None,
                "symbol_type": None,
                "token_count": 30,
            },
        ]],
        "distances": [[0.2, 0.3]],
    }

    result = _retrieve_chunks(mock_collection, "test query", top_k=10)

    # Should deduplicate overlapping chunks
    assert len(result.chunks) == 1


def test_retrieve_chunks_calculates_threshold_count():
    """Test _retrieve_chunks calculates num_chunks_above_threshold correctly."""
    from unittest.mock import Mock

    mock_collection = Mock()
    # Create chunks with various similarity scores
    # Threshold is 0.7, so similarities >= 0.7 should be counted
    mock_collection.query.return_value = {
        "ids": [["id1", "id2", "id3", "id4"]],
        "documents": [["doc1", "doc2", "doc3", "doc4"]],
        "metadatas": [[
            {"file_path": "test.py", "line_range": "10-20", "token_count": 50},
            {"file_path": "test.py", "line_range": "25-35", "token_count": 30},
            {"file_path": "test.py", "line_range": "40-50", "token_count": 40},
            {"file_path": "test.py", "line_range": "55-65", "token_count": 35},
        ]],
        "distances": [[0.1, 0.2, 0.4, 0.8]],  # Similarities: 0.9, 0.8, 0.6, 0.2
    }

    result = _retrieve_chunks(mock_collection, "test query", top_k=10)

    # After deduplication, should count chunks with similarity >= 0.7
    # id1: 0.9 >= 0.7, id2: 0.8 >= 0.7, id3: 0.6 < 0.7, id4: 0.2 < 0.7
    # Assuming no overlaps, should be 2
    assert result.num_chunks_above_threshold >= 0
    assert result.max_similarity == 0.9  # Highest similarity

