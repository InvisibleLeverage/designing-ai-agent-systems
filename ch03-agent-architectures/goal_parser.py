"""
Goal Parser — Chapter 3: Designing AI Agent Architectures

Parses a raw user goal into a structured ParsedGoal with subtasks,
success criteria, and clarification requirements.

Contract: parse_goal(raw_goal) → ParsedGoal
"""
import json
import os
from dataclasses import dataclass, field

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


@dataclass
class ParsedGoal:
    original: str
    clarified: str
    subtasks: list[str]
    success_criteria: list[str]
    estimated_steps: int
    requires_clarification: bool
    clarification_questions: list[str] = field(default_factory=list)


GOAL_PARSER_SYSTEM = """You are a goal-parsing engine. Given a user goal, output strict JSON with these fields:
{
  "requires_clarification": bool,
  "clarification_questions": [list of strings, empty if not needed],
  "clarified_goal": "restatement of the goal as a precise task",
  "subtasks": ["ordered list of subtasks, each a single actionable step"],
  "success_criteria": ["list of measurable conditions for task completion"],
  "estimated_steps": integer
}
Output ONLY valid JSON. No prose, no explanation."""


def parse_goal(raw_goal: str) -> ParsedGoal:
    """Parse a raw goal string into a structured ParsedGoal."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=GOAL_PARSER_SYSTEM,
        messages=[{"role": "user", "content": raw_goal}],
    )
    data = json.loads(response.content[0].text)
    return ParsedGoal(
        original=raw_goal,
        clarified=data["clarified_goal"],
        subtasks=data["subtasks"],
        success_criteria=data["success_criteria"],
        estimated_steps=data["estimated_steps"],
        requires_clarification=data["requires_clarification"],
        clarification_questions=data.get("clarification_questions", []),
    )


if __name__ == "__main__":
    goal = (
        "Research the market for AI-powered legal document review tools — "
        "top five players, pricing models, key differentiators. One-page briefing."
    )
    result = parse_goal(goal)
    print(f"Clarified: {result.clarified}")
    print(f"Subtasks ({len(result.subtasks)}):")
    for i, t in enumerate(result.subtasks, 1):
        print(f"  {i}. {t}")
    print(f"Estimated steps: {result.estimated_steps}")
    if result.requires_clarification:
        print("Clarification needed:")
        for q in result.clarification_questions:
            print(f"  - {q}")
