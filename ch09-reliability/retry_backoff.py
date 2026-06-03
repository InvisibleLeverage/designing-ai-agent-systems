"""
Retry with Exponential Backoff — Chapter 9: System Reliability and Safety

The only safe retry pattern for agent tool calls.
  delay = base_delay * 2^attempt + jitter(0, 0.5)

Never stack retry loops (tool-level + orchestrator-level) — blast radius multiplies.
Never use while True: retry() — that becomes a DDoS against your own dependencies.
"""
import asyncio
import random
import time
from functools import wraps
from typing import Callable, Optional, Type


class MaxRetriesExceeded(Exception):
    """Raised when all retry attempts are exhausted."""
    def __init__(self, attempts: int, last_error: Exception):
        self.attempts   = attempts
        self.last_error = last_error
        super().__init__(f"Failed after {attempts} attempts. Last error: {last_error}")


def with_retry(
    max_retries:       int   = 3,
    base_delay:        float = 1.0,
    max_delay:         float = 30.0,
    jitter_range:      float = 0.5,
    retryable_errors:  Optional[tuple[Type[Exception], ...]] = None,
):
    """
    Decorator: wrap a function with exponential backoff retry.
    On final attempt: re-raises the original exception (not MaxRetriesExceeded).
    Callers must decide whether to degrade gracefully or abort.

    Args:
        max_retries:      Number of retry attempts (not including the first call).
        base_delay:       Initial delay in seconds.
        max_delay:        Cap on delay regardless of backoff calculation.
        jitter_range:     Random jitter added to each delay (0, jitter_range).
        retryable_errors: Only retry these exception types. Default: retry all.
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    if retryable_errors and not isinstance(exc, retryable_errors):
                        raise   # non-retryable — re-raise immediately
                    last_exc = exc
                    if attempt == max_retries:
                        raise   # final attempt — re-raise original error
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, jitter_range), max_delay)
                    time.sleep(delay)
            raise MaxRetriesExceeded(max_retries + 1, last_exc)
        return wrapper
    return decorator


def with_retry_async(
    max_retries:       int   = 3,
    base_delay:        float = 1.0,
    max_delay:         float = 30.0,
    jitter_range:      float = 0.5,
    retryable_errors:  Optional[tuple[Type[Exception], ...]] = None,
):
    """Async version of with_retry for use with async/await."""
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    if retryable_errors and not isinstance(exc, retryable_errors):
                        raise
                    if attempt == max_retries:
                        raise
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, jitter_range), max_delay)
                    await asyncio.sleep(delay)
        return wrapper
    return decorator


def retry_call(
    fn:                Callable,
    *args,
    max_retries:       int   = 3,
    base_delay:        float = 1.0,
    retryable_errors:  Optional[tuple[Type[Exception], ...]] = None,
    **kwargs,
):
    """Functional form — call fn with retry without using the decorator."""
    decorated = with_retry(
        max_retries=max_retries,
        base_delay=base_delay,
        retryable_errors=retryable_errors,
    )(fn)
    return decorated(*args, **kwargs)


# ── Quick smoke test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    call_log: list[str] = []

    @with_retry(max_retries=3, base_delay=0.1, jitter_range=0.05)
    def flaky_api(query: str) -> dict:
        call_log.append(f"attempt at {time.time():.2f}")
        if len(call_log) < 3:
            raise ConnectionError(f"API unavailable (attempt {len(call_log)})")
        return {"result": f"success for: {query}"}

    try:
        result = flaky_api("test query")
        print(f"Succeeded on attempt {len(call_log)}: {result}")
    except ConnectionError as e:
        print(f"Failed after all retries: {e}")

    print(f"Call times: {call_log}")

    # Show backoff delays are exponential
    print("\nExpected delays (base=1s):")
    for attempt in range(3):
        delay = 1.0 * (2 ** attempt)
        print(f"  Attempt {attempt+1}: ~{delay:.1f}s + jitter")
