"""
Circuit Breaker — Chapter 9: System Reliability and Safety

States: CLOSED → OPEN (on threshold failures) → HALF_OPEN (after timeout) → CLOSED

Wire around every external dependency: model API, web search, database writes.
The goal is to fail fast when a dependency is degraded, not cascade slowly.
"""
import time
from enum import Enum


class State(Enum):
    CLOSED    = "closed"
    OPEN      = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout  = recovery_timeout
        self._state            = State.CLOSED
        self._failure_count    = 0
        self._opened_at: float = 0.0

    @property
    def state(self) -> State:
        if self._state == State.OPEN:
            if time.time() - self._opened_at >= self.recovery_timeout:
                self._state = State.HALF_OPEN
        return self._state

    def call(self, fn, *args, **kwargs):
        """Call fn through the circuit breaker."""
        current_state = self.state

        if current_state == State.OPEN:
            raise RuntimeError(
                f"Circuit breaker OPEN — dependency unavailable. "
                f"Retry after {self.recovery_timeout:.0f}s."
            )

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self._failure_count = 0
        self._state = State.CLOSED

    def _on_failure(self):
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._state    = State.OPEN
            self._opened_at = time.time()

    def status(self) -> dict:
        return {
            "state":          self.state.value,
            "failures":       self._failure_count,
            "threshold":      self.failure_threshold,
            "recovery_in_s":  max(0.0, self.recovery_timeout - (time.time() - self._opened_at))
                              if self._state == State.OPEN else 0.0,
        }
