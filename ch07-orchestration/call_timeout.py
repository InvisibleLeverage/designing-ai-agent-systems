"""
Call Timeout + Dead Letter Queue — Chapter 7: Multi-Agent Systems and Orchestration

Every agent-to-agent call gets a hard timeout. Tasks that exceed it go to a dead
letter queue — a persistent log for diagnosis and manual replay.

Alert when dead letter queue depth grows above zero in a rolling 5-minute window:
that indicates a deadlock forming, not a one-off failure.
"""
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class DeadLetterEntry:
    entry_id:    str   = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_id:     str   = ""
    payload:     dict  = field(default_factory=dict)
    timeout_at:  float = field(default_factory=time.time)
    timeout_s:   float = 0.0
    agent_fn:    str   = ""
    retry_count: int   = 0
    notes:       str   = ""


class DeadLetterQueue:
    """Persistent log of timed-out tasks. In-memory stub — swap for Redis/Postgres."""

    def __init__(self):
        self._entries: list[DeadLetterEntry] = []

    def push(self, entry: DeadLetterEntry) -> None:
        self._entries.append(entry)

    def depth(self) -> int:
        return len(self._entries)

    def recent(self, window_seconds: float = 300.0) -> list[DeadLetterEntry]:
        """Entries added within the last window_seconds (default 5 minutes)."""
        cutoff = time.time() - window_seconds
        return [e for e in self._entries if e.timeout_at >= cutoff]

    def is_alerting(self, window_seconds: float = 300.0) -> bool:
        """True when any entry landed in the rolling window — alert threshold."""
        return len(self.recent(window_seconds)) > 0

    def all_entries(self) -> list[DeadLetterEntry]:
        return list(self._entries)


# Global dead letter queue — shared across all calls in this process.
# In production: replace with a Redis list or Postgres table.
_dead_letter_queue = DeadLetterQueue()


async def call_with_timeout(
    agent_fn:     Callable,
    payload:      dict,
    timeout_s:    float = 90.0,
    task_id:      Optional[str] = None,
    dead_letter:  Optional[DeadLetterQueue] = None,
) -> Any:
    """
    Call an async agent function with a hard timeout.
    On TimeoutError: write to dead letter queue, then re-raise.
    Callers decide on retry vs. abort.

    Args:
        agent_fn:    Async callable — the agent or tool to call.
        payload:     Dict passed to agent_fn.
        timeout_s:   Hard timeout in seconds (default 90s).
        task_id:     Optional task identifier for tracing.
        dead_letter: Dead letter queue instance. Defaults to module-level queue.
    """
    dlq = dead_letter or _dead_letter_queue
    tid = task_id or str(uuid.uuid4())[:8]

    try:
        return await asyncio.wait_for(agent_fn(payload), timeout=timeout_s)
    except asyncio.TimeoutError:
        entry = DeadLetterEntry(
            task_id=tid,
            payload=payload,
            timeout_at=time.time(),
            timeout_s=timeout_s,
            agent_fn=getattr(agent_fn, "__name__", str(agent_fn)),
        )
        dlq.push(entry)
        raise   # caller decides: retry, degrade gracefully, or abort


def call_with_timeout_sync(
    agent_fn:    Callable,
    payload:     dict,
    timeout_s:   float = 90.0,
    task_id:     Optional[str] = None,
    dead_letter: Optional[DeadLetterQueue] = None,
) -> Any:
    """Synchronous wrapper around call_with_timeout for non-async callers."""
    return asyncio.run(call_with_timeout(agent_fn, payload, timeout_s, task_id, dead_letter))


def get_dead_letter_queue() -> DeadLetterQueue:
    return _dead_letter_queue


# ── Quick smoke test ──────────────────────────────────────────────────────────

async def _demo():
    dlq = DeadLetterQueue()

    async def fast_agent(payload: dict) -> dict:
        await asyncio.sleep(0.1)
        return {"result": "completed", "goal": payload.get("goal")}

    async def slow_agent(payload: dict) -> dict:
        await asyncio.sleep(10.0)    # will time out
        return {"result": "never reached"}

    # Fast call — should succeed
    result = await call_with_timeout(fast_agent, {"goal": "Quick task"}, timeout_s=2.0, dead_letter=dlq)
    print(f"Fast call succeeded: {result}")

    # Slow call — should time out and land in dead letter queue
    try:
        await call_with_timeout(slow_agent, {"goal": "Long running task"}, timeout_s=0.5, dead_letter=dlq)
    except asyncio.TimeoutError:
        print(f"Slow call timed out — DLQ depth: {dlq.depth()}")
        print(f"Alerting (5-min window): {dlq.is_alerting()}")
        entry = dlq.recent()[0]
        print(f"DLQ entry: task_id={entry.task_id}, timeout={entry.timeout_s}s, fn={entry.agent_fn}")


if __name__ == "__main__":
    asyncio.run(_demo())
