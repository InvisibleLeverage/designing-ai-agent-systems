"""
Quality Monitor — Chapter 10: System Observability and Operational Intelligence

Tracks output quality signals that infrastructure monitoring cannot see:
  - Confidence self-reporting distribution
  - Schema compliance rate
  - Hallucination detection (unverified claim rate)
  - Rolling pass-rate with week-over-week alerting
"""
import os
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Literal, Optional

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


# ── Data types ────────────────────────────────────────────────────────────────

ConfidenceLevel = Literal["HIGH", "MEDIUM", "LOW"]


@dataclass
class QualityRecord:
    task_id:         str
    timestamp:       float
    passed:          bool
    confidence:      Optional[ConfidenceLevel] = None
    schema_valid:    bool = True
    unverified_rate: float = 0.0   # fraction of claims without retrieved evidence
    notes:           str = ""


@dataclass
class WeeklyStats:
    pass_rate:       float
    high_confidence: float   # fraction of HIGH-confidence completions
    schema_rate:     float   # fraction passing schema validation
    mean_unverified: float   # average unverified-claim rate
    sample_count:    int


class QualityMonitor:
    """
    Rolling quality monitor. Records are kept for 14 days; alerts fire when
    7-day pass rate drops more than 5 percentage points vs the prior 7 days.
    """

    def __init__(self, window_days: int = 14, alert_threshold_pp: float = 5.0):
        self._window_sec   = window_days * 86_400
        self._alert_delta  = alert_threshold_pp / 100.0
        self._records: deque[QualityRecord] = deque()

    # ── Recording ────────────────────────────────────────────────────────────

    def record(self, record: QualityRecord) -> None:
        self._records.append(record)
        self._evict_old()

    def record_pass(
        self,
        task_id:         str,
        confidence:      Optional[ConfidenceLevel] = None,
        schema_valid:    bool = True,
        unverified_rate: float = 0.0,
    ) -> None:
        self.record(QualityRecord(
            task_id=task_id, timestamp=time.time(), passed=True,
            confidence=confidence, schema_valid=schema_valid,
            unverified_rate=unverified_rate,
        ))

    def record_fail(self, task_id: str, notes: str = "") -> None:
        self.record(QualityRecord(
            task_id=task_id, timestamp=time.time(), passed=False, notes=notes,
        ))

    # ── Analysis ─────────────────────────────────────────────────────────────

    def weekly_stats(self, days_back: float = 7.0) -> WeeklyStats:
        cutoff = time.time() - days_back * 86_400
        window = [r for r in self._records if r.timestamp >= cutoff]
        if not window:
            return WeeklyStats(0.0, 0.0, 0.0, 0.0, 0)
        n = len(window)
        return WeeklyStats(
            pass_rate       = sum(r.passed for r in window) / n,
            high_confidence = sum(r.confidence == "HIGH" for r in window) / n,
            schema_rate     = sum(r.schema_valid for r in window) / n,
            mean_unverified = sum(r.unverified_rate for r in window) / n,
            sample_count    = n,
        )

    def alert_check(self) -> list[str]:
        """Return a list of alert messages (empty list = healthy)."""
        alerts = []
        current = self.weekly_stats(days_back=7)
        prior   = self.weekly_stats(days_back=14)   # overlaps, but useful directional signal

        if current.sample_count < 5:
            return []   # not enough data

        if prior.pass_rate > 0 and (prior.pass_rate - current.pass_rate) >= self._alert_delta:
            alerts.append(
                f"PASS RATE DROP: {current.pass_rate:.1%} (current) vs "
                f"{prior.pass_rate:.1%} (prior) — "
                f"delta {(prior.pass_rate - current.pass_rate)*100:.1f}pp"
            )

        if current.high_confidence < 0.60:
            alerts.append(
                f"LOW CONFIDENCE: only {current.high_confidence:.1%} HIGH-confidence "
                f"completions (target ≥ 60%)"
            )

        if current.schema_rate < 0.98:
            alerts.append(
                f"SCHEMA COMPLIANCE: {current.schema_rate:.1%} (target ≥ 98%) — "
                f"possible prompt drift or model change"
            )

        if current.mean_unverified > 0.25:
            alerts.append(
                f"HALLUCINATION RISK: mean unverified claim rate {current.mean_unverified:.1%} "
                f"(target < 25%) — enter Silent Hallucination Zone watch"
            )

        return alerts

    # ── LLM-based confidence extraction ──────────────────────────────────────

    @staticmethod
    def extract_confidence(output: str) -> Optional[ConfidenceLevel]:
        """
        Ask the model to self-report confidence on its own output.
        Returns HIGH / MEDIUM / LOW, or None if classification fails.
        """
        prompt = (
            f"Rate the confidence of this AI-generated output.\n\n"
            f"OUTPUT:\n{output[:2000]}\n\n"
            f"Reply with exactly one word: HIGH, MEDIUM, or LOW.\n"
            f"HIGH = factually grounded, sources verifiable.\n"
            f"MEDIUM = mostly grounded with some inference.\n"
            f"LOW = speculative, unverifiable, or uncertain."
        )
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
        )
        word = response.content[0].text.strip().upper()
        return word if word in ("HIGH", "MEDIUM", "LOW") else None   # type: ignore[return-value]

    # ── Internal ─────────────────────────────────────────────────────────────

    def _evict_old(self) -> None:
        cutoff = time.time() - self._window_sec
        while self._records and self._records[0].timestamp < cutoff:
            self._records.popleft()


# ── Quick smoke test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    monitor = QualityMonitor()

    import random
    random.seed(42)
    for i in range(30):
        if random.random() > 0.15:
            monitor.record_pass(
                task_id=f"t{i}",
                confidence=random.choice(["HIGH", "HIGH", "MEDIUM", "LOW"]),
                unverified_rate=random.uniform(0.0, 0.3),
            )
        else:
            monitor.record_fail(task_id=f"t{i}", notes="output failed validation")

    import json
    stats = monitor.weekly_stats()
    print("Weekly stats:", json.dumps({
        "pass_rate":       f"{stats.pass_rate:.1%}",
        "high_confidence": f"{stats.high_confidence:.1%}",
        "schema_rate":     f"{stats.schema_rate:.1%}",
        "sample_count":    stats.sample_count,
    }, indent=2))

    alerts = monitor.alert_check()
    print("Alerts:", alerts or ["none — system healthy"])
