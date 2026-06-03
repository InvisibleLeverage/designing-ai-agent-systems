"""
Parallel Fan-out — Chapter 3: Designing AI Agent Architectures

Each subtask runs simultaneously via asyncio.gather.
After all complete, one synthesis call merges results into a structured output.

Pattern: decompose → fan-out → synthesize
"""
import asyncio
import json
import os

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))
MODEL = "claude-sonnet-4-6"


async def run_subtask(task: str, system: str = "Complete the assigned task concisely.") -> str:
    """Run a single subtask asynchronously."""
    response = await asyncio.to_thread(
        client.messages.create,
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": task}],
    )
    return response.content[0].text


async def parallel_fanout(subtasks: list[str], synthesis_goal: str) -> str:
    """
    Run all subtasks in parallel, then synthesize the results.

    Args:
        subtasks: List of task strings to run concurrently
        synthesis_goal: Instruction for combining all results

    Returns:
        Synthesized final output
    """
    # Fan-out: all subtasks run simultaneously
    results = await asyncio.gather(*[run_subtask(t) for t in subtasks])

    # Synthesize: one call to merge all results
    combined = "\n\n".join(
        f"### Result {i+1}\n{r}" for i, r in enumerate(results)
    )
    synthesis_prompt = f"{synthesis_goal}\n\n{combined}"

    response = await asyncio.to_thread(
        client.messages.create,
        model=MODEL,
        max_tokens=2048,
        system="Synthesize the provided research results into a single coherent report.",
        messages=[{"role": "user", "content": synthesis_prompt}],
    )
    return response.content[0].text


if __name__ == "__main__":
    companies = ["OpenAI", "Anthropic", "Google DeepMind"]
    tasks = [f"Summarize {c}'s main AI products and pricing in 3 bullet points." for c in companies]

    result = asyncio.run(parallel_fanout(
        subtasks=tasks,
        synthesis_goal="Combine these company summaries into a competitive landscape overview.",
    ))
    print(result)
