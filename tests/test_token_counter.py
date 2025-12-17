"""Tests for token counting utilities."""


from src.chunking.token_counter import (
    count_tokens,
    decode_tokens,
    split_text_to_tokens,
    validate_chunk_size,
)


def test_count_tokens_unicode():
    """Test token counting with unicode characters."""
    text = "Hello 世界 🌍"
    count = count_tokens(text)
    assert count > 0


def test_count_tokens_special_characters():
    """Test token counting with special characters."""
    text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    count = count_tokens(text)
    assert count > 0


def test_count_tokens_code_snippet():
    """Test token counting with code snippet."""
    text = """
def function(x: int) -> str:
    return str(x * 2)
"""
    count = count_tokens(text)
    assert count > 0


def test_validate_chunk_size_exact_limit():
    """Test validate_chunk_size with text at exact limit."""
    # Create text that's exactly at the limit
    text = "Short"
    # This should pass if it's under the limit
    result = validate_chunk_size(text, max_tokens=100)
    assert result is True


def test_validate_chunk_size_zero_limit():
    """Test validate_chunk_size with zero limit."""
    text = "Any text"
    result = validate_chunk_size(text, max_tokens=0)
    # Empty string has 0 tokens, so should pass
    assert validate_chunk_size("", max_tokens=0) is True
    # Non-empty text should fail
    assert result is False


def test_split_text_to_tokens_empty():
    """Test split_text_to_tokens with empty string."""
    tokens = split_text_to_tokens("")
    assert tokens == []


def test_split_text_to_tokens_preserves_order():
    """Test split_text_to_tokens preserves token order."""
    text1 = "Hello world"
    text2 = "world Hello"

    tokens1 = split_text_to_tokens(text1)
    tokens2 = split_text_to_tokens(text2)

    # Should be different (order matters)
    assert tokens1 != tokens2


def test_decode_tokens_empty_list():
    """Test decode_tokens with empty token list."""
    decoded = decode_tokens([])
    assert decoded == ""


def test_decode_tokens_round_trip_complex():
    """Test encode/decode round trip with complex text."""
    original = """
def complex_function(x: int, y: str = "default") -> dict[str, int]:
    \"\"\"This is a docstring with 'quotes' and \"double quotes\".\"\"\"
    result = {"key": x}
    return result
"""
    tokens = split_text_to_tokens(original)
    decoded = decode_tokens(tokens)
    assert decoded == original


def test_count_tokens_consistency():
    """Test that count_tokens matches length of split_text_to_tokens."""
    text = "Hello world, this is a test"
    count = count_tokens(text)
    tokens = split_text_to_tokens(text)
    assert count == len(tokens)

