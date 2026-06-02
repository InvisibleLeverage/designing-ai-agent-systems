"""
Cost Manager — Chapter 8: Deployment and Scaling

Tracks API spend at two levels: system-wide daily ceiling and per-user cap.
Call check_budget() before each task. Call record_usage() after each model call.
"""
import time
from dataclasses import dataclass, field
from threading import Lock


# Token pricing per 1M tokens (USD) — update as Anthropic adjusts pricing
PRICING = {
    "claude-haiku-4-5-20251001":  {"input": 0.80,  "output": 4.00},
    "claude-sonnet-4-6":          {"input": 3.00,  "output": 15.00},
    "claude-opus-4-8":            {"input": 15.00, "output": 75.00},
}


@dataclass
class UsageRecord:
    input_tokens:  int   = 0
    output_tokens: int   = 0
    cost_usd:      float = 0.0
    last_reset:    float = field(default_factory=time.time)


class CostManager:
    def __init__(
        self,
        daily_system_budget: float = 50.00,
        per_user_daily_cap:  float = 5.00,
    ):
        self._system_budget   = daily_system_budget
        self._user_cap        = per_user_daily_cap
        self._system: UsageRecord         = UsageRecord()
        self._users:  dict[str, UsageRecord] = {}
        self._lock = Lock()

    # ── Public API ──────────────────────────────────────────────────────────

    def check_budget(self, user_id: str) -> tuple[bool, str]:
        """Return (allowed, reason). Call before executing any task."""
        self._maybe_reset_day()
        with self._lock:
            if self._system.cost_usd >= self._system_budget:
                return False, f"System daily budget exhausted (${self._system_budget:.2f})"
            user = self._users.get(user_id, UsageRecord())
            if user.cost_usd >= self._user_cap:
                return False, f"User daily cap reached (${self._user_cap:.2f})"
        return True, "ok"

    def record_usage(
        self,
        user_id:       str,
        model:         str,
        input_tokens:  int,
        output_tokens: int,
    ) -> float:
        """Record token usage and return cost in USD for this call."""
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        with self._lock:
            self._system.input_tokens  += input_tokens
            self._system.output_tokens += output_tokens
            self._system.cost_usd      += cost

            if user_id not in self._users:
                self._users[user_id] = UsageRecord()
            u = self._users[user_id]
            u.input_tokens  += input_tokens
            u.output_tokens += output_tokens
            u.cost_usd      += cost
        return cost

    def status(self) -> dict:
        self._maybe_reset_day()
        with self._lock:
            return {
                "system": {
                    "cost_usd":      round(self._system.cost_usd, 4),
                    "budget_usd":    self._system_budget,
                    "remaining_usd": round(self._system_budget - self._system.cost_usd, 4),
                    "input_tokens":  self._system.input_tokens,
                    "output_tokens": self._system.output_tokens,
                },
                "active_users": len(self._users),
            }

    def user_status(self, user_id: str) -> dict:
        with self._lock:
            u = self._users.get(user_id, UsageRecord())
            return {
                "user_id":       user_id,
                "cost_usd":      round(u.cost_usd, 4),
                "cap_usd":       self._user_cap,
                "remaining_usd": round(self._user_cap - u.cost_usd, 4),
            }

    # ── Internals ────────────────────────────────────────────────────────────

    @staticmethod
    def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        rates = PRICING.get(model, PRICING["claude-sonnet-4-6"])
        return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000

    def _maybe_reset_day(self) -> None:
        """Reset counters if a calendar day has rolled over."""
        now = time.time()
        with self._lock:
            if now - self._system.last_reset >= 86_400:
                self._system = UsageRecord(last_reset=now)
                self._users  = {}


# ── Quick smoke test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    mgr = CostManager(daily_system_budget=10.00, per_user_daily_cap=2.00)

    allowed, reason = mgr.check_budget("user_1")
    print(f"Budget check: {allowed} — {reason}")

    cost = mgr.record_usage("user_1", "claude-sonnet-4-6", input_tokens=5_000, output_tokens=1_000)
    print(f"Call cost: ${cost:.4f}")

    print(mgr.status())
    print(mgr.user_status("user_1"))
