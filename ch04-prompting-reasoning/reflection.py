"""
Three-Pass Reflection — Chapter 4: Prompting and Reasoning Systems

Draft → Critique → Revise

Cost: 3× a single-pass call. Reserve for high-stakes outputs.
Hard cap on critique tokens prevents verbose critique loops.
"""
import os

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"

DRAFT_SYSTEM    = "Think step by step. Produce a thorough, well-structured analysis."
CRITIQUE_SYSTEM = "Find weaknesses, gaps, logical errors, and missing evidence in the draft. Be specific and critical."
REVISE_SYSTEM   = "Revise the draft to address every critique point. Improve the argument and fill the gaps."


def three_pass_reflection(task: str, context: str = "") -> dict:
    """
    Run a three-pass reflection loop on a task.

    Returns:
        {
            "draft": str,
            "critique": str,
            "final": str,
        }
    """
    user_input = f"{context}\n\n{task}".strip() if context else task

    # Pass 1: Draft
    draft_resp = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=DRAFT_SYSTEM,
        messages=[{"role": "user", "content": user_input}],
    )
    draft = draft_resp.content[0].text

    # Pass 2: Critique (hard cap prevents runaway verbosity)
    critique_resp = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=CRITIQUE_SYSTEM,
        messages=[{"role": "user", "content": draft}],
    )
    critique = critique_resp.content[0].text

    # Pass 3: Revise
    revise_input = (
        f"Original task: {task}\n\n"
        f"Draft:\n{draft}\n\n"
        f"Critique:\n{critique}\n\n"
        f"Revise to address the critique:"
    )
    revise_resp = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=REVISE_SYSTEM,
        messages=[{"role": "user", "content": revise_input}],
    )
    final = revise_resp.content[0].text

    return {"draft": draft, "critique": critique, "final": final}


if __name__ == "__main__":
    result = three_pass_reflection(
        task="Write an executive summary for why our company should invest in AI agent systems this year.",
        context="We are a 200-person B2B SaaS company in the legal tech space.",
    )
    print("=== FINAL OUTPUT ===")
    print(result["final"])
