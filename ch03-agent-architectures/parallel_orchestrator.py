"""
Parallel Orchestrator — Chapter 3: Designing AI Agent Architectures

Fan-out pattern: distribute independent subtasks across multiple agent instances
simultaneously via asyncio.gather(), then synthesise results into a single output.

Use when subtasks are independent (no shared state, no ordering dependency).
Do not use when subtask durations vary 10× or more — the slow tail dominates wall time.
"""
import asyncio
import os
import time
from dataclasses import dataclass, field

import anthropic

from agent_loop import run_agent

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL  = "claude-sonnet-4-6"


@dataclass
class SubtaskResult:
    subtask:      str
    result:       str
    duration_s:   float
    success:      bool
    error:        str = ""


@dataclass
class OrchestrationResult:
    subtasks_total:    int
    subtasks_succeeded: int
    synthesis:         str
    results:           list[SubtaskResult] = field(default_factory=list)
    total_duration_s:  float = 0.0


async def _run_subtask(subtask: str, max_steps: int = 10) -> SubtaskResult:
    """Run a single agent subtask asynchronously."""
    start = time.time()
    loop  = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, run_agent, subtask, None, max_steps)
        return SubtaskResult(subtask=subtask, result=result,
                             duration_s=round(time.time() - start, 2), success=True)
    except Exception as exc:
        return SubtaskResult(subtask=subtask, result="",
                             duration_s=round(time.time() - start, 2),
                             success=False, error=str(exc))


def _synthesise(subtask_results: list[SubtaskResult], synthesis_goal: str) -> str:
    """Merge successful subtask outputs into a single coherent response."""
    successful = [r for r in subtask_results if r.success]
    if not successful:
        return "All subtasks failed — no results to synthesise."

    context = "\n\n".join(
        f"[SUBTASK: {r.subtask}]\n{r.result}" for r in successful
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system="You are a synthesis agent. Combine multiple research outputs into a single coherent response. Remove duplication. Preserve specific facts and data.",
        messages=[{
            "role": "user",
            "content": (
                f"Synthesis goal: {synthesis_goal}\n\n"
                f"Subtask results to synthesise:\n{context}\n\n"
                f"Produce a unified response that integrates all results."
            ),
        }],
    )
    return response.content[0].text.strip()


async def run_parallel(
    subtasks:       list[str],
    synthesis_goal: str,
    max_steps:      int = 10,
) -> OrchestrationResult:
    """
    Fan-out: run all subtasks concurrently, then synthesise.

    Args:
        subtasks:       Independent tasks to run in parallel.
        synthesis_goal: What the merged output should achieve.
        max_steps:      Step cap per subtask agent.
    """
    start   = time.time()
    results = list(await asyncio.gather(*[_run_subtask(t, max_steps) for t in subtasks]))

    succeeded = [r for r in results if r.success]
    synthesis = _synthesise(results, synthesis_goal)

    return OrchestrationResult(
        subtasks_total=len(subtasks),
        subtasks_succeeded=len(succeeded),
        synthesis=synthesis,
        results=results,
        total_duration_s=round(time.time() - start, 2),
    )


if __name__ == "__main__":
    # Example: research 3 companies in parallel, synthesise into a comparison
    subtasks = [
        "Summarise Stripe's core product, business model, and recent growth in 3 sentences.",
        "Summarise Braintree's core product, business model, and market position in 3 sentences.",
        "Summarise Adyen's core product, business model, and market position in 3 sentences.",
    ]
    synthesis_goal = "A side-by-side comparison of three payment processors for an enterprise buyer."

    result = asyncio.run(run_parallel(subtasks, synthesis_goal))

    print(f"Subtasks: {result.subtasks_succeeded}/{result.subtasks_total} succeeded")
    print(f"Wall time: {result.total_duration_s}s\n")
    print("=== SYNTHESIS ===")
    print(result.synthesis[:600])
