"""Tests for retry decorator."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from src.utils.retry import _jitter_backoff, retry_gemini_api


def test_jitter_backoff_creates_wait_function():
    """Test _jitter_backoff creates a valid wait function."""
    wait_func = _jitter_backoff(base=1.0, max_delay=60.0)
    assert callable(wait_func)


def test_jitter_backoff_respects_max_delay():
    """Test _jitter_backoff respects max_delay parameter."""
    from tenacity import RetryCallState

    wait_func = _jitter_backoff(base=1.0, max_delay=10.0)

    # Create a mock retry call state with high attempt number
    mock_state = Mock(spec=RetryCallState)
    mock_state.outcome = Mock()
    mock_state.outcome.failed = True

    # Simulate many attempts (exponential would exceed max_delay)
    # Note: jitter can add randomness, so we allow small tolerance
    max_seen = 0.0
    for attempt in range(10):
        mock_state.attempt_number = attempt
        delay = wait_func(mock_state)
        max_seen = max(max_seen, delay)

    # With jitter, delay might slightly exceed max_delay, but should be close
    # Allow 15% tolerance for jitter randomness
    assert max_seen <= 10.0 * 1.15


def test_retry_gemini_api_decorates_function():
    """Test retry_gemini_api decorates a function."""
    @retry_gemini_api(max_attempts=3)
    def test_func():
        return "success"

    assert callable(test_func)
    assert test_func() == "success"


def test_retry_gemini_api_retries_on_exception():
    """Test retry_gemini_api retries on exceptions."""
    call_count = [0]

    @retry_gemini_api(max_attempts=3, base_delay=0.01, max_delay=0.1)
    def failing_func():
        call_count[0] += 1
        if call_count[0] < 3:
            raise Exception("Transient error")
        return "success"

    result = failing_func()
    assert result == "success"
    assert call_count[0] == 3


def test_retry_gemini_api_exhausts_attempts():
    """Test retry_gemini_api exhausts attempts and reraises."""
    call_count = [0]

    @retry_gemini_api(max_attempts=3, base_delay=0.01, max_delay=0.1)
    def always_failing_func():
        call_count[0] += 1
        raise Exception("Persistent error")

    with pytest.raises(Exception, match="Persistent error"):
        always_failing_func()

    assert call_count[0] == 3


def test_retry_gemini_api_works_with_async():
    """Test retry_gemini_api works with async functions."""
    call_count = [0]

    @retry_gemini_api(max_attempts=3, base_delay=0.01, max_delay=0.1)
    async def async_failing_func():
        call_count[0] += 1
        if call_count[0] < 2:
            raise Exception("Transient error")
        return "success"

    async def run_test():
        return await async_failing_func()

    result = asyncio.run(run_test())
    assert result == "success"
    assert call_count[0] == 2


def test_retry_gemini_api_custom_exceptions():
    """Test retry_gemini_api with custom exception types."""
    call_count = [0]

    class CustomException(Exception):
        pass

    @retry_gemini_api(max_attempts=3, base_delay=0.01, max_delay=0.1, exceptions=(CustomException,))
    def func_with_custom_exception():
        call_count[0] += 1
        if call_count[0] < 2:
            raise CustomException("Custom error")
        return "success"

    result = func_with_custom_exception()
    assert result == "success"
    assert call_count[0] == 2


def test_retry_gemini_api_does_not_retry_other_exceptions():
    """Test retry_gemini_api does not retry non-matching exceptions."""
    call_count = [0]

    class OtherException(Exception):
        pass

    @retry_gemini_api(max_attempts=3, base_delay=0.01, max_delay=0.1, exceptions=(ValueError,))
    def func_with_other_exception():
        call_count[0] += 1
        raise OtherException("Other error")

    with pytest.raises(OtherException):
        func_with_other_exception()

    # Should only be called once (no retries for non-matching exception)
    assert call_count[0] == 1

