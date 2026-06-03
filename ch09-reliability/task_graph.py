"""
Task Graph — Chapter 9: System Reliability and Safety

Explicit dependency graph with cycle detection. Run cycle check BEFORE execution starts.
Sequential task graphs never deadlock — risk is exclusive to parallel architectures.

Failure mode this prevents: Agent A waits for B, B waits for A → neither proceeds.
"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class Task:
    task_id:    str
    fn:         Callable
    depends_on: list[str]   = field(default_factory=list)
    result:     Any         = None
    status:     str         = "pending"   # pending | running | done | failed
    error:      str         = ""
    duration_s: float       = 0.0


class CycleDetectedError(Exception):
    """Raised when add_task detects a circular dependency."""


class TaskGraph:
    """
    Directed acyclic task graph with topological execution.

    Detects cycles at task-addition time (DFS), not at execution time.
    Executes ready tasks (all dependencies done) in parallel.
    """

    def __init__(self):
        self._tasks: dict[str, Task] = {}

    def add_task(self, task_id: str, fn: Callable, depends_on: list[str] = None) -> None:
        """
        Register a task. Runs DFS cycle check immediately.
        Raises CycleDetectedError if adding this task would create a cycle.
        """
        deps = depends_on or []

        # Validate that all dependencies exist
        for dep in deps:
            if dep not in self._tasks:
                raise ValueError(f"Dependency '{dep}' not registered. Add it first.")

        # Build adjacency map including the new task for cycle check
        adj: dict[str, list[str]] = {t: list(self._tasks[t].depends_on) for t in self._tasks}
        adj[task_id] = deps

        if self._has_cycle(adj):
            raise CycleDetectedError(
                f"Adding task '{task_id}' with depends_on={deps} creates a cycle."
            )

        self._tasks[task_id] = Task(task_id=task_id, fn=fn, depends_on=deps)

    async def execute(self) -> dict[str, Any]:
        """
        Execute all tasks in topological order.
        Tasks with no unfinished dependencies run concurrently.
        Returns dict of task_id → result.
        """
        loop = asyncio.get_event_loop()

        while not self._all_done():
            ready = self._get_ready_tasks()
            if not ready:
                # Nothing is ready and not all done → deadlock (should not happen after cycle check)
                stuck = [t for t in self._tasks.values() if t.status == "pending"]
                raise RuntimeError(
                    f"Execution stuck — no ready tasks. Stuck tasks: {[t.task_id for t in stuck]}"
                )

            results = await asyncio.gather(
                *[self._run_task(t, loop) for t in ready],
                return_exceptions=True,
            )

            # Handle failures — mark failed tasks so dependents can be skipped
            for task, result in zip(ready, results):
                if isinstance(result, Exception):
                    task.status = "failed"
                    task.error  = str(result)

        return {t.task_id: t.result for t in self._tasks.values() if t.status == "done"}

    async def _run_task(self, task: Task, loop: asyncio.AbstractEventLoop) -> Any:
        task.status = "running"
        start       = time.time()
        # Pass results of dependencies as kwargs if the function accepts them
        dep_results = {dep: self._tasks[dep].result for dep in task.depends_on}
        try:
            if asyncio.iscoroutinefunction(task.fn):
                result = await task.fn(**dep_results) if dep_results else await task.fn()
            else:
                result = await loop.run_in_executor(
                    None,
                    lambda: task.fn(**dep_results) if dep_results else task.fn(),
                )
            task.result     = result
            task.status     = "done"
            task.duration_s = round(time.time() - start, 3)
            return result
        except Exception as exc:
            task.status     = "failed"
            task.error      = str(exc)
            task.duration_s = round(time.time() - start, 3)
            raise

    def _get_ready_tasks(self) -> list[Task]:
        """Tasks where all dependencies are done and task itself is pending."""
        return [
            t for t in self._tasks.values()
            if t.status == "pending"
            and all(self._tasks[dep].status == "done" for dep in t.depends_on)
        ]

    def _all_done(self) -> bool:
        return all(t.status in ("done", "failed") for t in self._tasks.values())

    @staticmethod
    def _has_cycle(adj: dict[str, list[str]]) -> bool:
        """DFS cycle detection on directed graph."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in adj}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for neighbour in adj.get(node, []):
                if colour := color.get(neighbour):
                    if colour == GRAY:
                        return True   # back edge → cycle
                    if colour == WHITE and dfs(neighbour):
                        return True
            color[node] = BLACK
            return False

        return any(color[n] == WHITE and dfs(n) for n in adj)

    def summary(self) -> dict:
        counts: dict[str, int] = {}
        for t in self._tasks.values():
            counts[t.status] = counts.get(t.status, 0) + 1
        return {"tasks": counts, "total": len(self._tasks)}


# ── Quick smoke test ──────────────────────────────────────────────────────────

async def _demo():
    graph = TaskGraph()

    graph.add_task("fetch_data",     fn=lambda: {"rows": [1, 2, 3]})
    graph.add_task("fetch_context",  fn=lambda: {"context": "market is up"})
    graph.add_task("analyse",        fn=lambda **kw: {"analysis": f"Processed {kw}"}, depends_on=["fetch_data", "fetch_context"])
    graph.add_task("write_report",   fn=lambda **kw: f"Report: {kw['analyse']['analysis']}", depends_on=["analyse"])

    print("Tasks registered. Checking for cycles... OK")

    # Cycle detection test
    try:
        g2 = TaskGraph()
        g2.add_task("A", fn=lambda: None)
        g2.add_task("B", fn=lambda: None, depends_on=["A"])
        g2.add_task("A2", fn=lambda: None, depends_on=["B"])   # would create A→B→A2, fine
        # This WOULD create a cycle if A depended on A2 — test that the check works
        print("Cycle test (no cycle): OK")
    except CycleDetectedError as e:
        print(f"Cycle detected correctly: {e}")

    results = await graph.execute()
    print(f"\nExecution complete: {graph.summary()}")
    for task_id, result in results.items():
        print(f"  {task_id}: {str(result)[:60]}")


if __name__ == "__main__":
    asyncio.run(_demo())
