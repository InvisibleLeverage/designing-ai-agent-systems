"""
Context Management — Chapter 11: The Economics of Autonomous Systems

Two contracts:
  1. compress_tool_result() — shrink verbose tool output before adding to context
  2. manage_agent_context() — summarise old messages when context approaches the limit

Summarise BEFORE the context is full — not after, when coherence is already degraded.
"""
import os
from typing import Optional

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
HAIKU = "claude-haiku-4-5-20251001"

CHARS_PER_TOKEN     = 4     # rough approximation for budget estimation
MAX_TOOL_TOKENS     = 500   # tool results above this are compressed
MAX_CONTEXT_TOKENS  = 50_000


def compress_tool_result(result: str, tool_name: str, max_tokens: int = MAX_TOOL_TOKENS) -> str:
    """
    Compress a verbose tool result to fit within max_tokens.
    Preserves: facts, numbers, errors. Removes: boilerplate, repeated headers.

    Returns result unchanged if it already fits within budget.
    """
    estimated_tokens = len(result) / CHARS_PER_TOKEN
    if estimated_tokens <= max_tokens:
        return result

    prompt = (
        f"Compress this tool result from '{tool_name}' to under {max_tokens} tokens.\n\n"
        f"PRESERVE: all specific facts, numbers, errors, and structured data.\n"
        f"REMOVE: repeated headers, boilerplate, whitespace, and verbose descriptions.\n\n"
        f"Tool result:\n{result[:8000]}"
    )
    response = client.messages.create(
        model=HAIKU,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    summary = response.content[0].text.strip()
    return f"[COMPRESSED {tool_name} RESULT]\n{summary}"


def manage_agent_context(
    messages:          list[dict],
    max_context_tokens: int = MAX_CONTEXT_TOKENS,
    keep_recent:       int = 4,
) -> list[dict]:
    """
    Keep context within budget by summarising old messages with Haiku.

    Strategy:
      1. Estimate token count from character count.
      2. If within budget: return unchanged.
      3. If over budget: split into old (all except last keep_recent) and recent.
         Haiku summarises the old messages → inject as a summary message.
         Returns: [system_msg, summary_injection, *recent_messages]

    Note: Never summarises the system message (first message with role="system").
    The system message is always preserved verbatim.
    """
    estimated_tokens = sum(
        len(str(m.get("content", ""))) / CHARS_PER_TOKEN for m in messages
    )
    if estimated_tokens <= max_context_tokens:
        return messages

    # Separate system message (if present) from conversation
    if messages and messages[0].get("role") == "system":
        system_msg    = [messages[0]]
        conversation  = messages[1:]
    else:
        system_msg   = []
        conversation = messages

    if len(conversation) <= keep_recent:
        return messages   # nothing to summarise

    old_messages    = conversation[:-keep_recent]
    recent_messages = conversation[-keep_recent:]

    # Summarise the old messages
    history_text = "\n".join(
        f"[{m['role'].upper()}]: {str(m.get('content', ''))[:500]}"
        for m in old_messages
    )
    prompt = (
        f"Summarise this agent conversation history in under 400 tokens.\n\n"
        f"PRESERVE: decisions made, facts established, tool results, and task progress.\n"
        f"This summary replaces the original messages — completeness matters.\n\n"
        f"History:\n{history_text}"
    )
    response = client.messages.create(
        model=HAIKU,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    summary_text = response.content[0].text.strip()

    summary_injection = {
        "role":    "user",
        "content": (
            f"[CONVERSATION HISTORY SUMMARY — {len(old_messages)} prior messages compressed]\n"
            f"{summary_text}"
        ),
    }
    ack = {
        "role":    "assistant",
        "content": "Understood. I have the prior conversation context and will continue from here.",
    }

    return system_msg + [summary_injection, ack] + recent_messages


# ── Quick smoke test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test compress_tool_result
    verbose_result = """
HTTP/1.1 200 OK
Content-Type: application/json
X-Request-Id: abc123
Cache-Control: no-cache

{
  "company": "Acme Corp",
  "founded": 2015,
  "employees": 250,
  "revenue_2024": "$42M",
  "products": ["ProductA", "ProductB"],
  "ceo": "Jane Smith",
  "headquarters": "San Francisco, CA",
  "description": "Acme Corp is a leading provider of enterprise software solutions for mid-market companies. The company was founded in 2015 and has grown to 250 employees across offices in San Francisco, New York, and London. Their flagship products serve over 1,200 enterprise customers.",
  "recent_news": "Raised Series B of $18M in March 2024 led by Sequoia Capital."
}
""" * 5   # make it verbose enough to trigger compression

    compressed = compress_tool_result(verbose_result, "company_api")
    print(f"Original: ~{len(verbose_result)//4} tokens")
    print(f"Compressed: ~{len(compressed)//4} tokens")
    print(f"First 300 chars: {compressed[:300]}\n")

    # Test manage_agent_context
    messages = [
        {"role": "system", "content": "You are a research agent."},
        {"role": "user",      "content": "Research Acme Corp for an enterprise sales call."},
        {"role": "assistant", "content": "I'll research Acme Corp now."},
        {"role": "user",      "content": "[TOOL RESULT: web_search]\nAcme Corp is a B2B SaaS company..."},
        {"role": "assistant", "content": "Found key information. Checking competitors next."},
        {"role": "user",      "content": "[TOOL RESULT: web_search]\nTop competitors are X, Y, Z..."},
        {"role": "assistant", "content": "Now synthesising into a briefing."},
        {"role": "user",      "content": "What are their main pain points?"},
    ]

    managed = manage_agent_context(messages, max_context_tokens=100, keep_recent=3)
    print(f"Original messages: {len(messages)}")
    print(f"After management:  {len(managed)}")
    for m in managed:
        role    = m.get("role", "?")
        preview = str(m.get("content", ""))[:80].replace("\n", " ")
        print(f"  [{role:10s}] {preview}...")
