"""Retry utilities for Gemini API calls with exponential backoff and jitter.

This module provides retry decorators and helpers for handling transient errors
when communicating with Gemini's API, particularly for structured output failures
and embedding generation errors.
"""

import logging
from typing import Any, Callable, TypeVar

from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

# Type variable for generic functions
F = TypeVar("F", bound=Callable[..., Any])


def _jitter_backoff(base: float = 1, max_delay: float = 60) -> Callable[[RetryCallState], float]:
    """
    Create a wait function that combines exponential backoff with jitter.

    The delay formula is: min(base * 2^attempt + random(0, base * 2^attempt), max_delay)
    This provides exponential backoff with full jitter to avoid thundering herd.

    Args:
        base: Base delay in seconds (default: 1)
        max_delay: Maximum delay in seconds (default: 60)

    Returns:
        A wait function that can be used with tenacity.
    """
    return wait_exponential(multiplier=base, max=max_delay) + wait_random(0, base)


# Common exception types that should trigger retries for Gemini API calls
GEMINI_RETRY_EXCEPTIONS = (
    Exception,  # Broad catch for transient errors including EventLoopException
)


def retry_gemini_api(
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[Exception], ...] = GEMINI_RETRY_EXCEPTIONS,
) -> Callable[[F], F]:
    """
    Decorator to retry Gemini API calls with exponential backoff and jitter.

    This decorator is designed to handle transient errors from Gemini API calls,
    including structured output tool invocation failures (EventLoopException).

    Args:
        max_attempts: Maximum number of retry attempts (default: 5)
        base_delay: Base delay in seconds for exponential backoff (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exceptions: Tuple of exception types that should trigger retries
                    (default: catches all exceptions)

    Returns:
        Decorator function that can be applied to sync or async functions.

    Example:
        @retry_gemini_api(max_attempts=3)
        async def call_gemini_api():
            # API call here
            pass
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=_jitter_backoff(base=base_delay, max_delay=max_delay),
        retry=retry_if_exception_type(exceptions),
        reraise=True,
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )

