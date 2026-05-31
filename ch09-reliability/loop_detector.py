"""
Loop Detector — Chapter 9: System Reliability and Safety

Detects two failure modes:
  1. Step limit exceeded — agent ran too many steps
  2. Repeated identical tool calls — agent is looping

Call check() before every tool execution in the agent loop.
"""
import hashlib
import json
from collections import deque


class LoopDetector:
    def __init__(self, max_repeats: int = 3, max_steps: int = 25):
        self.max_repeats   = max_repeats
        self.max_steps     = max_steps
        self._step_count   = 0
        self._action_history: deque = deque(maxlen=max_steps)

    def check(self, tool_name: str, tool_input: dict) -> dict:
        """
        Returns {"loop_detected": bool, "message": str}.
        Call BEFORE executing every tool.
        """
        self._step_count += 1

        if self._step_count > self.max_steps:
            return {
                "loop_detected": True,
                "message": f"Step limit exceeded ({self.max_steps} steps). Task halted.",
            }

        fingerprint = hashlib.md5(
            json.dumps({"tool": tool_name, "input": tool_input}, sort_keys=True).encode()
        ).hexdigest()

        repeat_count = sum(1 for fp in self._action_history if fp == fingerprint)
        self._action_history.append(fingerprint)

        if repeat_count >= self.max_repeats:
            return {
                "loop_detected": True,
                "message": (
                    f"Loop detected: tool '{tool_name}' called with identical input "
                    f"{repeat_count + 1} times. Task halted."
                ),
            }

        return {"loop_detected": False, "message": ""}

    def reset(self):
        self._step_count = 0
        self._action_history.clear()
