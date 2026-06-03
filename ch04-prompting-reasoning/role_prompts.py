"""
Role Prompt Anatomy — Chapter 4: Prompting and Reasoning Systems

Three-component system prompt structure:
  1. Identity  — who the agent is
  2. Priorities — what it optimizes for, in order
  3. Output structure — what it returns and in what format

This produces consistent, predictable behavior at scale.
"""
import os
from dataclasses import dataclass

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))
MODEL = "claude-sonnet-4-6"


@dataclass
class RolePrompt:
    identity: str
    priorities: list[str]
    output_structure: str

    def render(self) -> str:
        priority_lines = "\n".join(f"{i+1}. {p}" for i, p in enumerate(self.priorities))
        return (
            f"{self.identity}\n\n"
            f"Priorities (in order):\n{priority_lines}\n\n"
            f"Output format:\n{self.output_structure}"
        )


# Pre-built role prompts from the book

SECURITY_REVIEWER = RolePrompt(
    identity="You are a senior security engineer with 15 years of experience in application and AI system security.",
    priorities=[
        "Flag injection risks first (prompt injection, SQL injection, command injection)",
        "Then authentication and authorization gaps",
        "Then data exposure and privacy risks",
        "Then general reliability concerns",
    ],
    output_structure='Return JSON: {"risk_level": "LOW|MEDIUM|HIGH", "findings": [...], "recommended_actions": [...]}',
)

RESEARCH_ANALYST = RolePrompt(
    identity="You are a senior research analyst with expertise in technology markets and competitive intelligence.",
    priorities=[
        "Accuracy over completeness — only state what you can verify",
        "Cite sources for all factual claims",
        "Flag uncertainty explicitly when present",
        "Structure findings for executive consumption",
    ],
    output_structure="Return a structured briefing: Executive Summary, Key Findings (bulleted), Recommendations, Sources.",
)

CODE_REVIEWER = RolePrompt(
    identity="You are a principal software engineer specializing in Python and distributed systems.",
    priorities=[
        "Correctness and safety first",
        "Then performance and scalability",
        "Then readability and maintainability",
        "Then style — only flag if it creates real confusion",
    ],
    output_structure='Return JSON: {"verdict": "APPROVE|REQUEST_CHANGES", "critical": [...], "suggestions": [...]}',
)


def call_with_role(prompt: str, role: RolePrompt, **kwargs) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=role.render(),
        messages=[{"role": "user", "content": prompt}],
        **kwargs,
    )
    return response.content[0].text


if __name__ == "__main__":
    review = call_with_role(
        "Review this system: an AI agent that autonomously sends customer emails "
        "based on CRM data. It runs every hour and personalizes each message.",
        role=SECURITY_REVIEWER,
    )
    print(review)
