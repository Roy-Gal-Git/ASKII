"""Token counting utilities using tiktoken."""

import tiktoken
from typing import List


# Use cl100k_base encoding (for GPT-4, GPT-3.5-turbo, suitable for general use)
_ENCODING_NAME = "cl100k_base"
_encoding = None


def _get_encoding() -> tiktoken.Encoding:
    """Get or create the tiktoken encoding."""
    global _encoding
    if _encoding is None:
        _encoding = tiktoken.get_encoding(_ENCODING_NAME)
    return _encoding


def count_tokens(text: str) -> int:
    """
    Count the number of tokens in a text string.

    Args:
        text: Input text to count tokens for

    Returns:
        int: Number of tokens
    """
    encoding = _get_encoding()
    tokens = encoding.encode(text)
    return len(tokens)


def validate_chunk_size(text: str, max_tokens: int = 300) -> bool:
    """
    Validate if text is within the maximum token limit.

    Args:
        text: Text to validate
        max_tokens: Maximum allowed tokens (default: 300)

    Returns:
        bool: True if text is within limit, False otherwise
    """
    token_count = count_tokens(text)
    return token_count <= max_tokens


def split_text_to_tokens(text: str) -> List[int]:
    """
    Split text into token IDs.

    Args:
        text: Input text

    Returns:
        List[int]: List of token IDs
    """
    encoding = _get_encoding()
    return encoding.encode(text)


def decode_tokens(tokens: List[int]) -> str:
    """
    Decode token IDs back to text.

    Args:
        tokens: List of token IDs

    Returns:
        str: Decoded text
    """
    encoding = _get_encoding()
    return encoding.decode(tokens)
