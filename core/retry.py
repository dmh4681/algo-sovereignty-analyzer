"""
Retry Utility Module - Centralized retry logic with exponential backoff.

Provides:
- retry_with_backoff(): Execute a callable with retry and exponential backoff
- with_retry(): Decorator factory for retrying functions automatically
- is_retryable_error(): Classify errors as transient vs permanent

Retry Strategy:
    Transient errors (retried with exponential backoff):
    - requests.exceptions.Timeout
    - requests.exceptions.ConnectionError
    - HTTP 429 (Rate Limited) - respects Retry-After header
    - HTTP 5xx (Server Errors: 500, 502, 503, 504)
    - Anthropic RateLimitError, APIConnectionError, InternalServerError

    Permanent errors (not retried):
    - HTTP 400 (Bad Request)
    - HTTP 404 (Not Found)
    - HTTP 401/403 (Authentication errors)
    - ValueError, TypeError, KeyError (programming errors)

Default Backoff Schedule (base_delay=1.0, max_retries=3):
    Attempt 1: immediate
    Attempt 2: ~1s delay
    Attempt 3: ~2s delay
    Attempt 4: ~4s delay
    Total max wait: ~7 seconds
"""

import logging
import time
import random
from functools import wraps
from typing import Callable, Optional

import requests

logger = logging.getLogger("core.retry")

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0   # seconds
DEFAULT_MAX_DELAY = 30.0   # seconds
DEFAULT_JITTER = True       # adds ≤10% random jitter to prevent thundering herd

# HTTP status codes that indicate a transient server-side failure
RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}

# Exception types that are always worth retrying (network-level)
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
)

# Exception types that indicate a programming or client error (never retry)
NON_RETRYABLE_EXCEPTIONS = (
    ValueError,
    TypeError,
    KeyError,
    AttributeError,
)


def is_retryable_error(exc: Exception) -> bool:
    """
    Classify whether an exception represents a transient error worth retrying.

    Args:
        exc: The exception to classify.

    Returns:
        True if the error is likely transient and the call should be retried.
    """
    # Programming/client errors are never transient
    if isinstance(exc, NON_RETRYABLE_EXCEPTIONS):
        return False

    # Network-level timeouts and connection failures are always transient
    if isinstance(exc, RETRYABLE_EXCEPTIONS):
        return True

    # HTTP errors: retry only on server-side status codes
    if isinstance(exc, requests.exceptions.HTTPError):
        response = getattr(exc, "response", None)
        if response is not None:
            return response.status_code in RETRYABLE_HTTP_CODES
        return False

    # Other requests library exceptions (e.g. ChunkedEncodingError) — retry
    if isinstance(exc, requests.exceptions.RequestException):
        return True

    # Anthropic SDK errors — check by class name to avoid hard import dependency
    exc_class = type(exc).__name__
    transient_anthropic = {
        "RateLimitError",
        "APIConnectionError",
        "InternalServerError",
        "ServiceUnavailableError",
        "APITimeoutError",
    }
    if exc_class in transient_anthropic:
        return True

    return False


def _extract_retry_after(exc: Exception) -> Optional[float]:
    """
    Extract the Retry-After delay (seconds) from a 429 HTTP response header.

    Returns None if not present or not parseable.
    """
    if isinstance(exc, requests.exceptions.HTTPError):
        response = getattr(exc, "response", None)
        if response is not None and response.status_code == 429:
            header_val = response.headers.get("Retry-After")
            if header_val:
                try:
                    return float(header_val)
                except (ValueError, TypeError):
                    pass
    return None


def retry_with_backoff(
    func: Callable,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    jitter: bool = DEFAULT_JITTER,
    retryable_check: Optional[Callable[[Exception], bool]] = None,
    operation_name: Optional[str] = None,
):
    """
    Execute a callable with exponential backoff retry logic.

    Args:
        func: Zero-argument callable to execute.
        max_retries: Maximum number of *retries* after the initial attempt
            (total attempts = max_retries + 1).
        base_delay: Delay (seconds) before the first retry; doubles each round.
        max_delay: Upper cap on the delay to avoid very long waits.
        jitter: If True, adds up to 10% random jitter to each delay to
            reduce thundering-herd effects.
        retryable_check: Optional custom function ``(exc) -> bool`` that
            overrides the default ``is_retryable_error`` classifier.
        operation_name: Human-readable name used in log messages.

    Returns:
        The return value of ``func()`` on success.

    Raises:
        The last exception raised by ``func()`` once all retries are exhausted,
        or immediately if the error is classified as non-retryable.
    """
    _check = retryable_check or is_retryable_error
    _name = operation_name or getattr(func, "__name__", "operation")

    last_exc: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as exc:
            last_exc = exc

            is_last_attempt = attempt == max_retries
            should_retry = _check(exc)

            if is_last_attempt or not should_retry:
                if attempt > 0:
                    logger.warning(
                        "%s failed after %d attempt(s): %s: %s",
                        _name,
                        attempt + 1,
                        type(exc).__name__,
                        exc,
                    )
                raise

            # Compute delay — honour Retry-After header on 429 responses
            retry_after = _extract_retry_after(exc)
            if retry_after is not None:
                delay = min(retry_after, max_delay)
                logger.info(
                    "%s rate-limited; retrying in %.1fs (attempt %d/%d)",
                    _name,
                    delay,
                    attempt + 1,
                    max_retries,
                )
            else:
                delay = min(base_delay * (2 ** attempt), max_delay)
                if jitter:
                    delay *= 1 + random.uniform(0, 0.1)
                logger.debug(
                    "%s attempt %d failed (%s); retrying in %.2fs",
                    _name,
                    attempt + 1,
                    type(exc).__name__,
                    delay,
                )

            time.sleep(delay)

    # Unreachable, but keeps type checkers happy
    raise last_exc  # type: ignore[misc]


def with_retry(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    jitter: bool = DEFAULT_JITTER,
    retryable_check: Optional[Callable[[Exception], bool]] = None,
):
    """
    Decorator factory that wraps a function with retry-with-backoff logic.

    Usage::

        @with_retry(max_retries=3, base_delay=1.0)
        def call_external_api():
            ...

    Args:
        max_retries: Maximum number of retries after the first attempt.
        base_delay: Initial delay in seconds (doubles each retry).
        max_delay: Maximum delay cap in seconds.
        jitter: Whether to add random jitter to delays.
        retryable_check: Custom ``(exc) -> bool`` classifier.

    Returns:
        A decorator that can be applied to any callable.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_with_backoff(
                func=lambda: func(*args, **kwargs),
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                jitter=jitter,
                retryable_check=retryable_check,
                operation_name=f"{func.__module__}.{func.__qualname__}",
            )
        return wrapper
    return decorator
