"""
Token Budget Manager — Chapter 8: Deployment and Scaling

Enforces per-category context allocations so one category never crowds out another.
The most common failure: tool result history grows unbounded and crushes reasoning space.

Default allocations target a 200K context window with 34K safety headroom.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CategoryBudget:
    allocated: int
    used:      int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.allocated - self.used)

    @property
    def utilization(self) -> float:
        return self.used / self.allocated if self.allocated else 0.0

    @property
    def is_exhausted(self) -> bool:
        return self.used >= self.allocated


DEFAULT_BUDGETS = {
    "system":    4_000,   # System prompt + persona           2%
    "task":      2_000,   # Current goal description          1%
    "memory":   20_000,   # RAG / retrieved context          10%
    "tools":    30_000,   # Accumulated tool call history    15%
    "reasoning":80_000,   # Active model reasoning space     40%
    "output":   30_000,   # Reserved for response generation 15%
    # 34K safety headroom not allocated — enforced by total cap
}

TOTAL_WINDOW = 200_000


class TokenBudgetManager:
    def __init__(self, budgets: Optional[dict[str, int]] = None):
        cfg = budgets or DEFAULT_BUDGETS
        self._budgets: dict[str, CategoryBudget] = {
            cat: CategoryBudget(allocated=alloc)
            for cat, alloc in cfg.items()
        }

    # ── Core API ─────────────────────────────────────────────────────────────

    def fits(self, category: str, tokens: int) -> bool:
        """Return True if tokens fit within the category's remaining allocation."""
        b = self._budgets.get(category)
        if b is None:
            raise ValueError(f"Unknown category '{category}'. Valid: {list(self._budgets)}")
        return tokens <= b.remaining

    def allocate(self, category: str, tokens: int) -> bool:
        """
        Consume tokens from category budget. Returns False (do not raise) when
        the category is exhausted — callers decide whether to truncate or abort.
        """
        b = self._budgets.get(category)
        if b is None:
            raise ValueError(f"Unknown category '{category}'")
        if tokens > b.remaining:
            return False
        b.used += tokens
        return True

    def force_allocate(self, category: str, tokens: int) -> int:
        """
        Allocate as many tokens as available. Returns actual tokens allocated.
        Use when truncation is preferable to rejection (e.g. memory chunks).
        """
        b = self._budgets[category]
        actual = min(tokens, b.remaining)
        b.used += actual
        return actual

    def reset(self, category: Optional[str] = None) -> None:
        """Reset one category or all categories."""
        if category:
            self._budgets[category].used = 0
        else:
            for b in self._budgets.values():
                b.used = 0

    # ── Reporting ────────────────────────────────────────────────────────────

    def utilization_report(self) -> dict:
        total_used = sum(b.used for b in self._budgets.values())
        report = {
            cat: {
                "allocated":   b.allocated,
                "used":        b.used,
                "remaining":   b.remaining,
                "utilization": f"{b.utilization:.1%}",
            }
            for cat, b in self._budgets.items()
        }
        report["_total"] = {
            "window":    TOTAL_WINDOW,
            "used":      total_used,
            "headroom":  TOTAL_WINDOW - total_used,
        }
        return report

    def is_context_critical(self, threshold: float = 0.90) -> bool:
        """True when any category is above threshold utilization."""
        return any(b.utilization >= threshold for b in self._budgets.values())

    def truncation_recommendation(self) -> list[str]:
        """Return categories that should be truncated (oldest-first eviction policy)."""
        return [
            cat for cat, b in self._budgets.items()
            if b.utilization >= 0.85
        ]


# ── Quick smoke test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    mgr = TokenBudgetManager()

    print("Allocating system prompt (3500 tokens):", mgr.allocate("system", 3_500))
    print("Allocating task (1800 tokens):",          mgr.allocate("task",   1_800))

    # Fill memory near limit
    for i in range(4):
        ok = mgr.allocate("memory", 4_500)
        print(f"  memory chunk {i+1}: {ok}")

    print("\nContext critical?", mgr.is_context_critical())
    print("Truncation candidates:", mgr.truncation_recommendation())

    import json
    print("\nUtilization report:")
    print(json.dumps(mgr.utilization_report(), indent=2))
