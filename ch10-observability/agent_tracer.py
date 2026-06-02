"""
Agent Tracer — Chapter 10: System Observability and Operational Intelligence

One structured trace record per agent step. All records for a task share task_id.

Swap the sink for:
  Prometheus push gateway  — latency / success histograms
  Langfuse                 — per-task trace with cost breakdown and tool call timeline
  S3 + Athena              — cost audit and long-term quality trend queries
"""
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Callable, Literal, Optional


# Sonnet pricing (USD per 1M tokens) — used for per-step cost calculation
_INPUT_RATE  = 3.00
_OUTPUT_RATE = 15.00


@dataclass
class TraceEvent:
    trace_id:     str    # same as task_id — the correlation key
    step:         int
    timestamp:    float
    action:       Literal["tool_call", "model_call", "retrieval", "validation", "task_complete"]
    duration_ms:  float

    # Optional per-action fields
    tool_name:     Optional[str]   = None
    model:         Optional[str]   = None
    input_tokens:  Optional[int]   = None
    output_tokens: Optional[int]   = None
    success:       bool            = True
    error_type:    Optional[str]   = None
    quality_score: float           = -1.0   # -1 = not yet evaluated

    @property
    def cost_usd(self) -> float:
        if self.input_tokens is None or self.output_tokens is None:
            return 0.0
        return (
            self.input_tokens  * _INPUT_RATE +
            self.output_tokens * _OUTPUT_RATE
        ) / 1_000_000

    def to_dict(self) -> dict:
        d = asdict(self)
        d["cost_usd"] = round(self.cost_usd, 6)
        return d


class AgentTracer:
    """
    Collects trace events for one task execution.
    Flush to a sink (stdout, Langfuse, S3) on task completion.
    """

    def __init__(self, task_id: Optional[str] = None, sink: Optional[Callable] = None):
        self.task_id  = task_id or str(uuid.uuid4())
        self._sink    = sink or (lambda event: print(json.dumps(event.to_dict(), indent=2)))
        self._events: list[TraceEvent] = []
        self._step    = 0

    # ── Convenience recorders ────────────────────────────────────────────────

    def record_model_call(
        self,
        duration_ms:   float,
        model:         str,
        input_tokens:  int,
        output_tokens: int,
        success:       bool = True,
        error_type:    Optional[str] = None,
    ) -> TraceEvent:
        return self._record(TraceEvent(
            trace_id=self.task_id, step=self._next_step(),
            timestamp=time.time(), action="model_call",
            duration_ms=duration_ms, model=model,
            input_tokens=input_tokens, output_tokens=output_tokens,
            success=success, error_type=error_type,
        ))

    def record_tool_call(
        self,
        tool_name:   str,
        duration_ms: float,
        success:     bool = True,
        error_type:  Optional[str] = None,
    ) -> TraceEvent:
        return self._record(TraceEvent(
            trace_id=self.task_id, step=self._next_step(),
            timestamp=time.time(), action="tool_call",
            duration_ms=duration_ms, tool_name=tool_name,
            success=success, error_type=error_type,
        ))

    def record_retrieval(
        self,
        duration_ms:   float,
        chunks_fetched: int,
        chunks_used:   int,
        success:       bool = True,
    ) -> TraceEvent:
        e = self._record(TraceEvent(
            trace_id=self.task_id, step=self._next_step(),
            timestamp=time.time(), action="retrieval",
            duration_ms=duration_ms, success=success,
        ))
        e.quality_score = chunks_used / chunks_fetched if chunks_fetched else 0.0
        return e

    def record_task_complete(
        self,
        duration_ms:   float,
        quality_score: float = -1.0,
    ) -> TraceEvent:
        return self._record(TraceEvent(
            trace_id=self.task_id, step=self._next_step(),
            timestamp=time.time(), action="task_complete",
            duration_ms=duration_ms, quality_score=quality_score,
        ))

    # ── Summary ──────────────────────────────────────────────────────────────

    def summary(self) -> dict:
        total_cost    = sum(e.cost_usd for e in self._events)
        total_tokens  = sum((e.input_tokens or 0) + (e.output_tokens or 0) for e in self._events)
        tool_errors   = sum(1 for e in self._events if e.action == "tool_call" and not e.success)
        model_calls   = sum(1 for e in self._events if e.action == "model_call")
        tool_calls    = sum(1 for e in self._events if e.action == "tool_call")
        total_ms      = sum(e.duration_ms for e in self._events)
        return {
            "task_id":       self.task_id,
            "total_steps":   self._step,
            "model_calls":   model_calls,
            "tool_calls":    tool_calls,
            "tool_errors":   tool_errors,
            "total_tokens":  total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "total_ms":      round(total_ms, 1),
        }

    def flush(self) -> None:
        """Emit all events to the configured sink."""
        for event in self._events:
            self._sink(event)

    # ── Internal ────────────────────────────────────────────────────────────

    def _next_step(self) -> int:
        self._step += 1
        return self._step

    def _record(self, event: TraceEvent) -> TraceEvent:
        self._events.append(event)
        return event


# ── Quick smoke test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    tracer = AgentTracer(task_id="task-demo-001")

    tracer.record_model_call(duration_ms=1240, model="claude-sonnet-4-6",
                             input_tokens=2_500, output_tokens=450)
    tracer.record_tool_call(tool_name="web_search", duration_ms=850)
    tracer.record_retrieval(duration_ms=120, chunks_fetched=10, chunks_used=6)
    tracer.record_model_call(duration_ms=2100, model="claude-sonnet-4-6",
                             input_tokens=8_200, output_tokens=1_200)
    tracer.record_task_complete(duration_ms=4310, quality_score=0.82)

    print("=== Task Summary ===")
    import json
    print(json.dumps(tracer.summary(), indent=2))

    print("\n=== Flushing events ===")
    tracer.flush()
