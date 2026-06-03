"""
Circuit Breaker — Chapter 8: Deployment and Scaling

Per-tool circuit breaker registry for agent deployment.
Wire around every external dependency: model API, web search, DB writes, third-party tools.
When any dependency is OPEN, return a degraded result immediately — never block the pipeline.

States: CLOSED → OPEN (on threshold failures) → HALF_OPEN (after timeout) → CLOSED
"""
import time
from enum import Enum
from threading import Lock


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
        self._opened_at        = 0.0
        self._success_count    = 0   # successes in HALF_OPEN before closing
        self._lock             = Lock()

    @property
    def state(self) -> State:
        with self._lock:
            if self._state == State.OPEN:
                if time.time() - self._opened_at >= self.recovery_timeout:
                    self._state = State.HALF_OPEN
            return self._state

    def call(self, fn, *args, **kwargs):
        """Call fn through the circuit breaker. Raises RuntimeError when OPEN."""
        current = self.state
        if current == State.OPEN:
            raise RuntimeError(
                f"Circuit breaker OPEN — dependency unavailable. "
                f"Retry after {self._seconds_until_recovery():.0f}s."
            )
        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._state         = State.CLOSED

    def _on_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._state     = State.OPEN
                self._opened_at = time.time()

    def _seconds_until_recovery(self) -> float:
        return max(0.0, self.recovery_timeout - (time.time() - self._opened_at))

    def status(self) -> dict:
        return {
            "state":           self.state.value,
            "failures":        self._failure_count,
            "threshold":       self.failure_threshold,
            "recovery_in_s":   self._seconds_until_recovery() if self._state == State.OPEN else 0.0,
        }

    def reset(self) -> None:
        with self._lock:
            self._state         = State.CLOSED
            self._failure_count = 0
            self._opened_at     = 0.0


class ToolCircuitBreakerRegistry:
    """
    Per-tool circuit breaker registry for agent deployment.
    Each external dependency gets its own breaker — failures in one tool
    don't trip breakers for other tools.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self._default_threshold = failure_threshold
        self._default_timeout   = recovery_timeout
        self._breakers:  dict[str, CircuitBreaker] = {}
        self._lock = Lock()

    def get(self, tool_name: str) -> CircuitBreaker:
        """Get (or create) the circuit breaker for a tool."""
        with self._lock:
            if tool_name not in self._breakers:
                self._breakers[tool_name] = CircuitBreaker(
                    failure_threshold=self._default_threshold,
                    recovery_timeout=self._default_timeout,
                )
            return self._breakers[tool_name]

    def call(self, tool_name: str, fn, *args, **kwargs):
        """
        Call fn through the tool's circuit breaker.
        Returns degraded result dict if OPEN — never blocks the pipeline.
        """
        breaker = self.get(tool_name)
        try:
            return breaker.call(fn, *args, **kwargs)
        except RuntimeError as exc:
            # Circuit is OPEN — return degraded result immediately
            return {"error": str(exc), "degraded": True, "tool": tool_name}

    def all_statuses(self) -> dict:
        return {name: cb.status() for name, cb in self._breakers.items()}

    def open_breakers(self) -> list[str]:
        return [name for name, cb in self._breakers.items() if cb.state == State.OPEN]


# ── Quick smoke test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    registry = ToolCircuitBreakerRegistry(failure_threshold=3, recovery_timeout=5.0)

    def flaky_search(query: str) -> dict:
        raise ConnectionError("Search API unavailable")

    def stable_db(query: str) -> dict:
        return {"rows": [{"id": 1}]}

    # Trip the search breaker
    for i in range(4):
        result = registry.call("web_search", flaky_search, "AI agents")
        print(f"Call {i+1}: {result}")

    print(f"\nOpen breakers: {registry.open_breakers()}")
    print(f"Stable DB still works: {registry.call('database', stable_db, 'SELECT 1')}")
    print(f"\nAll statuses: {registry.all_statuses()}")
