"""
Model Router — Chapter 8: Deployment and Scaling

Routes tasks to the appropriate model tier based on complexity signals.
Routing to Haiku instead of Sonnet on eligible tasks cuts costs ~75%.
Apply expensive models only where quality difference justifies the cost.

Tiers:
  Haiku  — extraction, classification, simple summarization
  Sonnet — reasoning chains, multi-step tasks, standard generation
  Opus   — long synthesis, novel planning, high-stakes judgment
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ModelTier(str, Enum):
    HAIKU  = "claude-haiku-4-5-20251001"
    SONNET = "claude-sonnet-4-6"
    OPUS   = "claude-opus-4-8"


@dataclass
class RoutingDecision:
    model:  ModelTier
    reason: str
    tier:   str   # "fast" | "standard" | "premium"


# Signals that elevate tier — checked in order (first match wins)
_OPUS_SIGNALS = [
    "synthesize", "long synthesis", "novel", "unprecedented", "strategic",
    "architectural decision", "evaluate tradeoffs",
]
_HAIKU_SIGNALS = [
    "extract", "classify", "categorize", "parse", "format", "translate",
    "summarize this", "bullet points", "list the", "how many", "count",
    "yes or no", "true or false",
]


class ModelRouter:
    def __init__(
        self,
        default_tier: ModelTier = ModelTier.SONNET,
        max_output_for_haiku: int = 1_000,
        min_output_for_opus:  int = 5_000,
    ):
        self._default           = default_tier
        self._haiku_output_cap  = max_output_for_haiku
        self._opus_output_floor = min_output_for_opus

    def route(
        self,
        task: str,
        expected_output_tokens: Optional[int] = None,
        force_tier: Optional[ModelTier] = None,
    ) -> RoutingDecision:
        """Select a model for the given task. Returns a RoutingDecision."""
        if force_tier:
            return RoutingDecision(model=force_tier, reason="forced override", tier="override")

        task_lower = task.lower()

        # Output length signals
        if expected_output_tokens is not None:
            if expected_output_tokens >= self._opus_output_floor:
                return RoutingDecision(
                    model=ModelTier.OPUS,
                    reason=f"long output expected ({expected_output_tokens} tokens)",
                    tier="premium",
                )
            if expected_output_tokens <= self._haiku_output_cap:
                return self._check_content_signals(task_lower) or RoutingDecision(
                    model=ModelTier.HAIKU,
                    reason=f"short output ({expected_output_tokens} tokens)",
                    tier="fast",
                )

        # Content signals — Opus
        for signal in _OPUS_SIGNALS:
            if signal in task_lower:
                return RoutingDecision(
                    model=ModelTier.OPUS,
                    reason=f"complexity signal: '{signal}'",
                    tier="premium",
                )

        # Content signals — Haiku
        for signal in _HAIKU_SIGNALS:
            if signal in task_lower:
                return RoutingDecision(
                    model=ModelTier.HAIKU,
                    reason=f"simple-task signal: '{signal}'",
                    tier="fast",
                )

        return RoutingDecision(model=self._default, reason="default tier", tier="standard")

    def _check_content_signals(self, task_lower: str) -> Optional[RoutingDecision]:
        for signal in _OPUS_SIGNALS:
            if signal in task_lower:
                return RoutingDecision(
                    model=ModelTier.OPUS,
                    reason=f"complexity signal overrides short-output heuristic: '{signal}'",
                    tier="premium",
                )
        return None

    @staticmethod
    def estimated_cost(
        model: ModelTier,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate USD cost for a single call."""
        rates = {
            ModelTier.HAIKU:  (0.80,  4.00),
            ModelTier.SONNET: (3.00,  15.00),
            ModelTier.OPUS:   (15.00, 75.00),
        }
        inp_rate, out_rate = rates[model]
        return (input_tokens * inp_rate + output_tokens * out_rate) / 1_000_000


# ── Quick smoke test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    router = ModelRouter()

    tasks = [
        "Extract the invoice number from this document",
        "Classify this support ticket into one of 8 categories",
        "Write a 3-step reasoning chain to evaluate this architecture decision",
        "Synthesize findings across 50 research papers into a strategic recommendation",
        "Summarize this paragraph in bullet points",
        "Plan a novel multi-agent orchestration pattern for this use case",
    ]

    for task in tasks:
        d = router.route(task)
        print(f"  {d.tier:8s}  {d.model.split('-')[1]:6s}  {d.reason}")
        print(f"           → {task[:60]}")
        print()
