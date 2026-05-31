"""
Hierarchical Orchestrator — Chapter 7: Multi-Agent Systems and Orchestration

Orchestrator decomposes goal → specialist agents execute subtasks → synthesize.
Subtasks with depends_on get prior results injected.
"""
import json
import os

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"

SPECIALIST_PROMPTS = {
    "research":  "You are a research specialist. Find accurate information and cite sources.",
    "analysis":  "You are an analysis specialist. Identify patterns, gaps, and key insights.",
    "writing":   "You are a writing specialist. Produce clear, structured, publication-ready text.",
    "code":      "You are a software engineer. Write clean, working, well-commented Python code.",
}

DECOMPOSE_SYSTEM = """Break the goal into a list of subtasks. Return strict JSON:
[
  {
    "id": "task_1",
    "description": "what this subtask does",
    "agent_type": "research|analysis|writing|code",
    "depends_on": []
  }
]
Order subtasks by dependency. Output only valid JSON — no prose."""


class HierarchicalOrchestrator:
    def decompose_goal(self, goal: str) -> list[dict]:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=DECOMPOSE_SYSTEM,
            messages=[{"role": "user", "content": goal}],
        )
        return json.loads(response.content[0].text)

    def execute_subtask(self, subtask: dict, completed: dict[str, str]) -> str:
        context = ""
        if subtask.get("depends_on"):
            prior = "\n\n".join(
                f"[{dep}]: {completed[dep]}" for dep in subtask["depends_on"] if dep in completed
            )
            context = f"Prior work:\n{prior}\n\n"
        prompt = f"{context}Task: {subtask['description']}"
        system = SPECIALIST_PROMPTS.get(subtask["agent_type"], SPECIALIST_PROMPTS["writing"])
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def run(self, goal: str) -> dict:
        subtasks = self.decompose_goal(goal)
        completed: dict[str, str] = {}

        for subtask in subtasks:
            completed[subtask["id"]] = self.execute_subtask(subtask, completed)

        # Final synthesis
        results_text = "\n\n".join(f"[{k}]\n{v}" for k, v in completed.items())
        final = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system="Synthesize all subtask outputs into a final, cohesive deliverable.",
            messages=[{"role": "user", "content": f"Goal: {goal}\n\n{results_text}"}],
        )

        return {
            "goal": goal,
            "subtasks_completed": len(subtasks),
            "individual_results": completed,
            "final_output": final.content[0].text,
        }
