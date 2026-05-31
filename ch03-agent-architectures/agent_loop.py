"""
Agent Loop — Chapter 3: Designing AI Agent Architectures

Three exits, nothing else:
  1. stop_reason == "end_turn"  → model declared complete
  2. stop_reason == "tool_use"  → execute tool, append result, continue
  3. step == max_steps          → log and return partial result

Business logic belongs in tools and system prompt — never in the loop.
"""
import json
import os

import anthropic

from tool_library import TOOLS, dispatch_tool

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"

DEFAULT_SYSTEM = """You are a helpful AI agent. You have access to tools to help complete tasks.
Think step by step. Use tools when you need current information or to perform actions.
When you have completed the task, provide a clear final answer."""


def run_agent(
    goal: str,
    system_prompt: str = DEFAULT_SYSTEM,
    max_steps: int = 20,
    tools: list = TOOLS,
) -> str:
    """Run the agent loop until completion, step limit, or error."""
    messages = [{"role": "user", "content": goal}]
    step = 0

    while step < max_steps:
        step += 1
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )

        # Exit 1: model declared complete
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        # Exit 2: tool use requested
        if response.stop_reason == "tool_use":
            # Append assistant turn
            messages.append({"role": "assistant", "content": response.content})

            # Execute all tool calls in this turn
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason — treat as complete
        break

    # Exit 3: step limit
    print(f"[agent_loop] Step limit reached ({max_steps}). Returning partial result.")
    for block in response.content:
        if hasattr(block, "text"):
            return block.text
    return ""


if __name__ == "__main__":
    result = run_agent(
        "What time is it right now, and what is 2 + 2?",
        max_steps=5,
    )
    print("Result:", result)
