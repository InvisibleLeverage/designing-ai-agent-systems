"""
Agent Evaluator — Chapter 9: System Reliability and Safety

LLM-as-judge evaluation framework. Run on sampled production tasks (1–5%)
to surface Silent Degradation before users notice it.

Rolling 7-day pass rate per task type: alert when it drops > 5pp below prior week.
"""
import json
import os
from typing import Optional

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


# Rubric library — each task type has evaluation criteria scored 0.0–1.0
RUBRICS: dict[str, list[str]] = {
    "research": [
        "Answers the specific question asked (not a related but different question)",
        "Claims are grounded in retrieved sources, not training memory",
        "Acknowledges gaps or uncertainty where data is missing",
        "Key facts are accurate and not contradicted by the sources",
    ],
    "extraction": [
        "All requested fields are present in the output",
        "Values match the source document (no hallucinated numbers or names)",
        "Output format matches the requested schema",
        "Missing fields are explicitly flagged as null, not silently omitted",
    ],
    "generation": [
        "Output addresses the goal stated in the input",
        "Tone and voice match the requested style",
        "No factual claims that contradict the input context",
        "Output length is appropriate — not padded, not truncated",
    ],
    "classification": [
        "Category assigned matches the most appropriate available option",
        "Reasoning provided for the classification",
        "Edge cases are flagged rather than forced into a category",
    ],
    "summarisation": [
        "Key information from the source is preserved",
        "No information is added that was not in the source",
        "Length is appropriate for the use case",
        "Important caveats or uncertainties in the source are preserved",
    ],
}


class AgentEvaluator:
    """
    Evaluates agent outputs against task-type rubrics.
    Uses Haiku for cost efficiency — designed for high-volume production sampling.
    """

    def __init__(self, custom_rubrics: Optional[dict[str, list[str]]] = None):
        self._rubrics = {**RUBRICS, **(custom_rubrics or {})}

    def evaluate(
        self,
        task_type:  str,
        input_text: str,
        output:     str,
        reference:  str = "",
    ) -> dict:
        """
        Evaluate a single output against its task rubric.

        Args:
            task_type:  One of the rubric keys (research, extraction, generation, ...).
            input_text: The original goal or input given to the agent.
            output:     The agent's output to evaluate.
            reference:  Optional known-good reference output for comparison.

        Returns:
            {"scores": {criterion: 0-1}, "overall": float, "flags": [...], "task_type": str}
        """
        rubric = self._rubrics.get(task_type)
        if rubric is None:
            return {"error": f"Unknown task_type '{task_type}'. Available: {list(self._rubrics)}"}

        criteria_text = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(rubric))
        ref_section   = f"\nREFERENCE OUTPUT:\n{reference[:1000]}" if reference else ""

        prompt = (
            f"Evaluate this AI agent output against the rubric criteria.\n\n"
            f"TASK TYPE: {task_type}\n"
            f"INPUT: {input_text[:500]}\n"
            f"AGENT OUTPUT:\n{output[:1500]}"
            f"{ref_section}\n\n"
            f"RUBRIC CRITERIA (score each 0.0–1.0):\n{criteria_text}\n\n"
            f"Respond in JSON:\n"
            f'{{"scores": {{"criterion_1": 0.0-1.0, ...}}, '
            f'"overall": 0.0-1.0, '
            f'"flags": ["any concern worth surfacing"]}}'
        )

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        try:
            result             = json.loads(raw)
            result["task_type"] = task_type
            return result
        except json.JSONDecodeError:
            return {"error": "judge parse error", "task_type": task_type,
                    "scores": {}, "overall": 0.0, "flags": []}

    def batch_evaluate(
        self,
        samples: list[dict],
    ) -> dict:
        """
        Evaluate a batch of samples. Each sample is a dict with:
            task_type, input_text, output, reference (optional).
        Returns aggregate stats + individual results.
        """
        results   = [self.evaluate(**s) for s in samples]
        valid     = [r for r in results if "error" not in r]
        avg_score = sum(r.get("overall", 0) for r in valid) / max(len(valid), 1)
        all_flags = [f for r in valid for f in r.get("flags", [])]

        return {
            "samples_evaluated": len(results),
            "avg_overall_score": round(avg_score, 3),
            "pass_rate":         f"{sum(1 for r in valid if r.get('overall', 0) >= 0.7)/max(len(valid),1):.0%}",
            "top_flags":         list(dict.fromkeys(all_flags))[:5],
            "results":           results,
        }

    def available_rubrics(self) -> list[str]:
        return list(self._rubrics.keys())


# ── Quick smoke test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    evaluator = AgentEvaluator()
    print(f"Available rubrics: {evaluator.available_rubrics()}\n")

    result = evaluator.evaluate(
        task_type="research",
        input_text="What are the main reliability challenges in multi-agent systems?",
        output=(
            "Multi-agent systems face reliability challenges at coordination boundaries. "
            "Key issues include: agent handoff failures (when one agent passes work to another "
            "without sufficient context), cascading failures (one agent's error propagating), "
            "and circuit breaker absence (no protection against slow downstream agents). "
            "Based on production deployments, the most common failure is context loss at handoff."
        ),
    )

    print(f"Overall score: {result.get('overall', 0):.2f}")
    print(f"Scores: {result.get('scores', {})}")
    print(f"Flags:  {result.get('flags', [])}")
