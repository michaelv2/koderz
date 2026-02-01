"""Retry utilities for handling transient failures with exponential backoff."""

import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Any
import requests

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryableError(Exception):
    """Base class for errors that should trigger a retry."""
    pass


class MaxRetriesExceeded(Exception):
    """Raised when maximum retry attempts are exceeded."""
    pass


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple = (
        requests.exceptions.ReadTimeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError,
    )
):
    """
    Decorator that retries a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        backoff_factor: Multiplier for delay on each retry (default: 2.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        retryable_exceptions: Tuple of exception types to retry on

    Raises:
        MaxRetriesExceeded: When all retry attempts are exhausted

    Example:
        @retry_with_backoff(max_retries=3, initial_delay=2.0)
        def make_api_call():
            return requests.get("https://api.example.com")
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except retryable_exceptions as e:
                    last_exception = e

                    # Check if it's a 503 Service Unavailable or timeout
                    is_retryable = False
                    if isinstance(e, requests.exceptions.HTTPError):
                        if e.response is not None and e.response.status_code in [503, 429]:
                            is_retryable = True
                    elif isinstance(e, (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError)):
                        is_retryable = True

                    if not is_retryable:
                        # Not a retryable error, re-raise immediately
                        raise

                    # If this was the last attempt, don't retry
                    if attempt >= max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}"
                        )
                        raise MaxRetriesExceeded(
                            f"Failed after {max_retries + 1} attempts: {e}"
                        ) from last_exception

                    # Log retry attempt
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    # Wait before retrying
                    time.sleep(delay)

                    # Calculate next delay with exponential backoff
                    delay = min(delay * backoff_factor, max_delay)

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def is_ollama_overloaded(error: Exception) -> bool:
    """
    Check if an error indicates Ollama is overloaded.

    Args:
        error: Exception to check

    Returns:
        True if error indicates server overload, False otherwise
    """
    if isinstance(error, requests.exceptions.HTTPError):
        if error.response is not None:
            return error.response.status_code in [503, 429]

    if isinstance(error, requests.exceptions.ReadTimeout):
        return True

    return False


def wait_for_ollama_capacity(
    host: str = "http://localhost:11434",
    timeout: float = 300.0,
    check_interval: float = 5.0
) -> bool:
    """
    Wait for Ollama to have capacity to handle requests.

    Args:
        host: Ollama server URL
        timeout: Maximum time to wait in seconds
        check_interval: Time between checks in seconds

    Returns:
        True if Ollama is ready, False if timeout exceeded
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Try to get server status
            response = requests.get(f"{host}/api/tags", timeout=5.0)
            if response.status_code == 200:
                return True
        except Exception:
            pass

        time.sleep(check_interval)

    return False
