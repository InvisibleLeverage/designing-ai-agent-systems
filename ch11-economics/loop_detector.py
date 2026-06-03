"""
Loop Detector — Chapter 11: The Economics of Autonomous Systems

Detects infinite reasoning loops before they exhaust budgets.
Two signals: step count ceiling and repeated action fingerprints.

Integration: call check() before every tool execution in the agent loop.
  if result["loop_detected"]: return {"error": result["message"]}
"""
import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class LoopDetector:
    """
    Stateful detector for one agent task execution.
    Create a new instance per task; do not reuse across tasks.
    """
    max_repeats: int = 3    # same action fingerprint this many times → loop
    max_steps:   int = 25   # hard step ceiling

    _step_count:     int             = field(default=0,                init=False)
    _action_history: list[str]       = field(default_factory=list,     init=False)
    _fingerprint_counts: Counter     = field(default_factory=Counter,  init=False)

    def check(self, tool_name: str, tool_input: dict) -> dict:
        """
        Check whether this tool call constitutes a loop.
        Call BEFORE executing the tool.

        Returns:
            {"loop_detected": False}                           — safe to proceed
            {"loop_detected": True, "message": str, "type": str}  — abort this task
        """
        self._step_count += 1

        # Signal 1: step ceiling
        if self._step_count > self.max_steps:
            return {
                "loop_detected": True,
                "message": f"Step limit exceeded: {self._step_count} steps (max {self.max_steps})",
                "type":    "step_limit",
            }

        # Signal 2: repeated action fingerprint
        fingerprint = self._fingerprint(tool_name, tool_input)
        self._action_history.append(fingerprint)
        self._fingerprint_counts[fingerprint] += 1

        if self._fingerprint_counts[fingerprint] >= self.max_repeats:
            return {
                "loop_detected": True,
                "message": (
                    f"Repeated action detected: '{tool_name}' called with identical inputs "
                    f"{self._fingerprint_counts[fingerprint]} times (max {self.max_repeats})"
                ),
                "type": "repeated_action",
            }

        return {"loop_detected": False}

    def step_count(self) -> int:
        return self._step_count

    def most_repeated_action(self) -> tuple[str, int]:
        """Returns (fingerprint, count) of the most-repeated action."""
        if not self._fingerprint_counts:
            return ("", 0)
        fp, count = self._fingerprint_counts.most_common(1)[0]
        return (fp, count)

    def summary(self) -> dict:
        return {
            "steps":            self._step_count,
            "unique_actions":   len(self._fingerprint_counts),
            "total_actions":    len(self._action_history),
            "max_repeat_count": self.most_repeated_action()[1],
        }

    @staticmethod
    def _fingerprint(tool_name: str, tool_input: dict) -> str:
        """MD5 of (tool_name + sorted tool_input). Identical calls → identical fingerprint."""
        payload = json.dumps({"tool": tool_name, "input": tool_input}, sort_keys=True, default=str)
        return hashlib.md5(payload.encode()).hexdigest()[:12]  # noqa: S324


# ── Quick smoke test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    detector = LoopDetector(max_repeats=3, max_steps=10)

    # Simulate normal execution
    actions = [
        ("web_search",  {"query": "AI agent architectures"}),
        ("web_search",  {"query": "multi-agent reliability"}),
        ("read_file",   {"path": "/data/report.pdf"}),
    ]
    for tool, inputs in actions:
        result = detector.check(tool, inputs)
        print(f"Step {detector.step_count()}: {tool} → loop_detected={result['loop_detected']}")

    print()

    # Simulate a stuck loop — same search repeated
    detector2 = LoopDetector(max_repeats=3, max_steps=10)
    stuck_action = ("web_search", {"query": "latest data"})

    for i in range(5):
        result = detector2.check(*stuck_action)
        print(f"Step {detector2.step_count()}: {stuck_action[0]} → loop_detected={result['loop_detected']}", end="")
        if result["loop_detected"]:
            print(f"  ⚠ {result['message']}")
            break
        else:
            print()

    print(f"\nSummary: {detector2.summary()}")
