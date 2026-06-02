"""
Retrieval Health — Chapter 10: System Observability and Operational Intelligence

Detects Retrieval Drift: gradual degradation in retrieval quality as corpus grows,
embedding models update, or query distribution shifts.

Symptoms are soft (slightly less relevant results, more hedging) — none trigger
infrastructure alerts. This module surfaces them before users notice.

Metrics tracked:
  - Similarity score distribution (weekly rolling)
  - Retrieval utilisation rate (chunks fetched vs chunks used)
  - Low-relevance query rate (queries where top-k score < threshold)
"""
import time
from collections import deque
from dataclasses import dataclass


# Alert thresholds
SIMILARITY_DRIFT_THRESHOLD  = 0.05   # alert if mean similarity drops > 5pp vs baseline
UTILISATION_FLOOR           = 0.40   # alert if < 40% of fetched chunks are used
LOW_RELEVANCE_RATE_CEILING  = 0.20   # alert if > 20% of queries score below MIN_SIM
MIN_SIMILARITY_SCORE        = 0.65   # below this = low relevance


@dataclass
class RetrievalEvent:
    timestamp:        float
    query_id:         str
    chunks_fetched:   int
    chunks_used:      int
    top_similarity:   float          # highest cosine score in this retrieval
    mean_similarity:  float          # mean across top-k chunks
    latency_ms:       float


class RetrievalHealthMonitor:
    """
    Maintains a rolling window of retrieval events and surfaces drift signals.
    Baseline is established from the first `baseline_min_samples` events.
    """

    def __init__(self, window_days: int = 14, baseline_min_samples: int = 100):
        self._window_sec   = window_days * 86_400
        self._baseline_min = baseline_min_samples
        self._events: deque[RetrievalEvent] = deque()
        self._baseline_mean_sim: float | None = None

    # ── Recording ────────────────────────────────────────────────────────────

    def record(
        self,
        query_id:        str,
        chunks_fetched:  int,
        chunks_used:     int,
        top_similarity:  float,
        mean_similarity: float,
        latency_ms:      float = 0.0,
    ) -> None:
        event = RetrievalEvent(
            timestamp=time.time(), query_id=query_id,
            chunks_fetched=chunks_fetched, chunks_used=chunks_used,
            top_similarity=top_similarity, mean_similarity=mean_similarity,
            latency_ms=latency_ms,
        )
        self._events.append(event)
        self._evict_old()
        self._update_baseline()

    # ── Health report ────────────────────────────────────────────────────────

    def health_report(self) -> dict:
        events = list(self._events)
        if not events:
            return {"status": "no_data", "event_count": 0}

        n = len(events)
        mean_sim  = sum(e.mean_similarity for e in events) / n
        mean_util = sum(e.chunks_used / max(e.chunks_fetched, 1) for e in events) / n
        low_rel   = sum(1 for e in events if e.top_similarity < MIN_SIMILARITY_SCORE) / n
        mean_lat  = sum(e.latency_ms for e in events) / n

        alerts = []
        if self._baseline_mean_sim is not None:
            drift = self._baseline_mean_sim - mean_sim
            if drift >= SIMILARITY_DRIFT_THRESHOLD:
                alerts.append(
                    f"RETRIEVAL DRIFT: mean similarity dropped {drift:.3f} "
                    f"(baseline {self._baseline_mean_sim:.3f} → current {mean_sim:.3f})"
                )

        if mean_util < UTILISATION_FLOOR:
            alerts.append(
                f"LOW UTILISATION: only {mean_util:.1%} of fetched chunks used "
                f"(threshold {UTILISATION_FLOOR:.0%}) — possible context flooding"
            )

        if low_rel > LOW_RELEVANCE_RATE_CEILING:
            alerts.append(
                f"HIGH LOW-RELEVANCE RATE: {low_rel:.1%} of queries score below "
                f"{MIN_SIMILARITY_SCORE} — corpus or embedding drift likely"
            )

        return {
            "status":            "alert" if alerts else "healthy",
            "event_count":       n,
            "mean_similarity":   round(mean_sim, 4),
            "baseline_sim":      round(self._baseline_mean_sim, 4) if self._baseline_mean_sim else None,
            "mean_utilisation":  f"{mean_util:.1%}",
            "low_relevance_rate":f"{low_rel:.1%}",
            "mean_latency_ms":   round(mean_lat, 1),
            "alerts":            alerts,
        }

    def similarity_percentiles(self) -> dict:
        """Return p25/p50/p75/p95 of top-similarity scores for charting."""
        scores = sorted(e.top_similarity for e in self._events)
        if not scores:
            return {}
        n = len(scores)
        def p(pct: float) -> float:
            return scores[int(n * pct / 100)]
        return {
            "p25": round(p(25), 4),
            "p50": round(p(50), 4),
            "p75": round(p(75), 4),
            "p95": round(p(95), 4),
        }

    # ── Internal ─────────────────────────────────────────────────────────────

    def _update_baseline(self) -> None:
        if self._baseline_mean_sim is None and len(self._events) >= self._baseline_min:
            first_n = list(self._events)[:self._baseline_min]
            self._baseline_mean_sim = sum(e.mean_similarity for e in first_n) / self._baseline_min

    def _evict_old(self) -> None:
        cutoff = time.time() - self._window_sec
        while self._events and self._events[0].timestamp < cutoff:
            self._events.popleft()


# ── Quick smoke test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import random
    random.seed(7)
    monitor = RetrievalHealthMonitor(baseline_min_samples=20)

    # Simulate a healthy baseline (high similarity scores)
    for i in range(20):
        monitor.record(
            query_id=f"q{i}",
            chunks_fetched=10, chunks_used=random.randint(5, 8),
            top_similarity=random.uniform(0.82, 0.95),
            mean_similarity=random.uniform(0.78, 0.90),
            latency_ms=random.uniform(80, 150),
        )

    # Simulate post-embedding-update degradation
    for i in range(20, 40):
        monitor.record(
            query_id=f"q{i}",
            chunks_fetched=10, chunks_used=random.randint(2, 5),
            top_similarity=random.uniform(0.60, 0.75),
            mean_similarity=random.uniform(0.55, 0.70),
            latency_ms=random.uniform(90, 160),
        )

    import json
    print(json.dumps(monitor.health_report(), indent=2))
    print("\nSimilarity percentiles:", monitor.similarity_percentiles())
