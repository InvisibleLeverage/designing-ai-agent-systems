"""
Agent Task Queue — Chapter 7: Multi-Agent Systems and Orchestration

Priority queue with retry logic and async worker pool.
Swap queue backend for Redis Streams, SQS, or RabbitMQ in deployment.

Priority tiers: 1=urgent, 2=normal, 3=batch.
Lower number = higher urgency (processed first).
"""
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class AgentTask:
    task_id:     str   = field(default_factory=lambda: str(uuid.uuid4())[:12])
    payload:     dict  = field(default_factory=dict)
    priority:    int   = 2          # 1=urgent, 2=normal, 3=batch
    max_retries: int   = 3
    attempt:     int   = 0
    status:      str   = "pending"  # pending → running → done | failed
    result:      dict  = field(default_factory=dict)
    created_at:  float = field(default_factory=time.time)
    started_at:  Optional[float] = None
    completed_at: Optional[float] = None
    error:       str   = ""

    def duration_s(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return round(self.completed_at - self.started_at, 3)
        return None


class AgentTaskQueue:
    """
    Async priority task queue with retry logic and configurable worker pool.

    Usage:
        queue = AgentTaskQueue(worker_fn=my_agent_runner, num_workers=4)
        task_id = await queue.submit(AgentTask(payload={"goal": "..."}))
        result  = await queue.wait_for(task_id)
    """

    def __init__(
        self,
        worker_fn:   Callable[[AgentTask], Any],
        num_workers: int   = 3,
        retry_delay: float = 2.0,   # base delay for exponential backoff
    ):
        self._worker_fn    = worker_fn
        self._num_workers  = num_workers
        self._retry_delay  = retry_delay
        self._queue:  asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks:  dict[str, AgentTask]  = {}
        self._running = False

    # ── Public API ────────────────────────────────────────────────────────────

    async def submit(self, task: AgentTask) -> str:
        """Enqueue a task. Returns task_id immediately — does not wait for completion."""
        self._tasks[task.task_id] = task
        # PriorityQueue orders by first element of tuple; use (priority, timestamp) for FIFO within tier
        await self._queue.put((task.priority, task.created_at, task.task_id))
        return task.task_id

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        return self._tasks.get(task_id)

    async def wait_for(self, task_id: str, poll_interval: float = 0.2) -> AgentTask:
        """Poll until the task reaches done or failed status."""
        while True:
            task = self._tasks.get(task_id)
            if task and task.status in ("done", "failed"):
                return task
            await asyncio.sleep(poll_interval)

    def stats(self) -> dict:
        counts: dict[str, int] = {}
        for t in self._tasks.values():
            counts[t.status] = counts.get(t.status, 0) + 1
        return {
            "queue_depth": self._queue.qsize(),
            "tasks":       counts,
            "total":       len(self._tasks),
        }

    # ── Worker lifecycle ──────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the worker pool. Call once; workers run until stop() is called."""
        self._running = True
        workers = [asyncio.create_task(self._worker(i)) for i in range(self._num_workers)]
        await asyncio.gather(*workers, return_exceptions=True)

    async def stop(self) -> None:
        self._running = False

    async def _worker(self, worker_id: int) -> None:
        while self._running:
            try:
                priority, created_at, task_id = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue

            task = self._tasks.get(task_id)
            if task is None:
                continue

            task.status     = "running"
            task.started_at = time.time()
            task.attempt   += 1

            try:
                loop   = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self._worker_fn, task)
                task.result       = result if isinstance(result, dict) else {"output": result}
                task.status       = "done"
                task.completed_at = time.time()
            except Exception as exc:
                task.error = str(exc)
                if task.attempt < task.max_retries:
                    # Exponential backoff before re-queuing
                    delay = self._retry_delay * (2 ** (task.attempt - 1))
                    await asyncio.sleep(delay)
                    task.status = "pending"
                    await self._queue.put((task.priority, time.time(), task_id))
                else:
                    task.status       = "failed"
                    task.completed_at = time.time()

            self._queue.task_done()


# ── Quick smoke test ──────────────────────────────────────────────────────────

async def _demo():
    def mock_worker(task: AgentTask) -> dict:
        import random
        time.sleep(random.uniform(0.1, 0.3))
        return {"processed": task.payload.get("goal", "unknown")}

    q = AgentTaskQueue(worker_fn=mock_worker, num_workers=2)

    tasks = [
        AgentTask(payload={"goal": "Research competitor A"},   priority=2),
        AgentTask(payload={"goal": "Urgent: fix prod bug"},    priority=1),
        AgentTask(payload={"goal": "Batch: update docs"},      priority=3),
        AgentTask(payload={"goal": "Research competitor B"},   priority=2),
    ]

    # Submit all tasks
    ids = [await q.submit(t) for t in tasks]
    print(f"Submitted {len(ids)} tasks")

    # Run workers until all tasks done
    async def run_until_done():
        worker_task = asyncio.create_task(q.start())
        while True:
            await asyncio.sleep(0.2)
            stats = q.stats()
            if stats["tasks"].get("pending", 0) == 0 and stats["queue_depth"] == 0:
                if stats["tasks"].get("running", 0) == 0:
                    break
        await q.stop()
        worker_task.cancel()

    await run_until_done()

    for task_id in ids:
        t = q.get_task(task_id)
        print(f"  [{t.priority}] {t.payload['goal'][:40]:40s}  {t.status:6s}  {t.duration_s()}s")

    print(f"\nFinal stats: {q.stats()}")


if __name__ == "__main__":
    asyncio.run(_demo())
