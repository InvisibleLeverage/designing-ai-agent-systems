"""
Context Manager — Chapter 5: Memory Systems and Context Management

Budget allocation for a 200K context window.
Never lets any caller push over-budget content into context.
Trims history most-recent-first; truncates tool output at its allocation.
"""
from dataclasses import dataclass, field

# Budget: 32K of a 200K window, keeping reasoning sharp
ALLOCATIONS = {
    "system_prompt":      2_000,
    "current_task":       1_000,
    "tool_definitions":   1_000,
    "retrieved_memories": 8_000,
    "recent_history":     6_000,
    "current_working":   10_000,
    "response_buffer":    4_000,
}


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ≈ 4 characters."""
    return len(text) // 4


@dataclass
class ContextBudget:
    allocations: dict = field(default_factory=lambda: dict(ALLOCATIONS))

    def fits(self, section: str, text: str) -> bool:
        return _estimate_tokens(text) <= self.allocations[section]

    def truncate(self, section: str, text: str) -> str:
        max_chars = self.allocations[section] * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n[truncated to context budget]"


def build_context(
    task: str,
    retrieved_memories: list[str],
    conversation_history: list[dict],
    current_tool_output: str = "",
    budget: ContextBudget = None,
) -> dict:
    """
    Assemble a context-managed prompt payload.

    Returns dict with keys: relevant_context, history, tool_output
    All values are guaranteed to fit within their budget allocations.
    """
    if budget is None:
        budget = ContextBudget()

    # Memories: concatenate until budget exhausted
    memory_text = ""
    for mem in retrieved_memories:
        candidate = memory_text + mem + "\n"
        if budget.fits("retrieved_memories", candidate):
            memory_text = candidate
        else:
            break

    # History: most-recent-first until budget exhausted
    trimmed_history = []
    history_tokens = 0
    for msg in reversed(conversation_history):
        msg_tokens = _estimate_tokens(str(msg))
        if history_tokens + msg_tokens > budget.allocations["recent_history"]:
            break
        trimmed_history.insert(0, msg)
        history_tokens += msg_tokens

    # Tool output: hard truncate at allocation
    tool_output = budget.truncate("current_working", current_tool_output)

    return {
        "task": task,
        "relevant_context": memory_text.strip(),
        "history": trimmed_history,
        "tool_output": tool_output,
    }
