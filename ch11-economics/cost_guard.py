"""
Cost-Guarded Task Runner — Chapter 11: The Economics of Autonomous Systems

Tracks per-task API cost and elapsed time.
Halts execution before runaway costs occur.

Integration: call check_limits() before each API call in the agent loop.
"""
import time
from dataclasses import dataclass, field

# Pricing per 1M tokens (as of 2025 — update as Anthropic pricing changes)
PRICING = {
    "claude-haiku-4-5-20251001":  {"input": 0.25,  "output": 1.25},
    "claude-sonnet-4-6":          {"input": 3.00,  "output": 15.00},
    "claude-opus-4-8":            {"input": 15.00, "output": 75.00},
}


@dataclass
class CostGuardedTaskRunner:
    max_cost_usd:   float = 2.0
    max_minutes:    float = 5.0
    model:          str   = "claude-sonnet-4-6"
    cost_incurred:  float = field(default=0.0, init=False)
    _start_time:    float = field(default=0.0, init=False)

    def start(self) -> None:
        """Reset counters for a new task."""
        self.cost_incurred = 0.0
        self._start_time   = time.time()

    def record_call(self, input_tokens: int, output_tokens: int, model: str = None) -> float:
        """Accumulate cost for one API call. Returns incremental cost."""
        m = model or self.model
        prices = PRICING.get(m, PRICING["claude-sonnet-4-6"])
        cost = (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000
        self.cost_incurred += cost
        return cost

    def check_limits(self) -> dict:
        """Returns {"exceeded": bool, "reason": str}. Call before every API call."""
        if self.cost_incurred >= self.max_cost_usd:
            return {
                "exceeded": True,
                "reason":   f"Cost limit reached: ${self.cost_incurred:.4f} >= ${self.max_cost_usd}",
            }
        elapsed_minutes = (time.time() - self._start_time) / 60
        if elapsed_minutes >= self.max_minutes:
            return {
                "exceeded": True,
                "reason":   f"Time limit reached: {elapsed_minutes:.1f}m >= {self.max_minutes}m",
            }
        return {"exceeded": False, "reason": ""}

    def get_summary(self) -> dict:
        return {
            "total_cost_usd":  round(self.cost_incurred, 6),
            "elapsed_seconds": round(time.time() - self._start_time, 1),
            "within_limits":   self.cost_incurred < self.max_cost_usd,
        }
