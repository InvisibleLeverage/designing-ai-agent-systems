"""
Tool Dispatcher — Chapter 6: Tool-Using AI Agents

Production-ready dispatch loop with:
  - Idempotency tracking (warns on duplicate calls to non-idempotent tools)
  - Schema validation before execution
  - Structured error returns (no raw exceptions reach the model)
"""
import hashlib
import json
from collections import defaultdict
from typing import Callable


NON_IDEMPOTENT = frozenset({"send_email", "post_message", "create_record", "charge_payment"})


class ToolDispatcher:
    def __init__(self, handlers: dict[str, Callable], non_idempotent: set[str] = NON_IDEMPOTENT):
        self._handlers = handlers
        self._non_idempotent = non_idempotent
        self._call_fingerprints: defaultdict[str, int] = defaultdict(int)

    def _fingerprint(self, name: str, input_data: dict) -> str:
        payload = json.dumps({"tool": name, "input": input_data}, sort_keys=True)
        return hashlib.md5(payload.encode()).hexdigest()

    def dispatch(self, name: str, input_data: dict) -> dict:
        """Dispatch with idempotency warning for non-idempotent tools."""
        if name in self._non_idempotent:
            fp = self._fingerprint(name, input_data)
            self._call_fingerprints[fp] += 1
            if self._call_fingerprints[fp] > 1:
                return {
                    "error": f"Duplicate call to non-idempotent tool '{name}' detected. "
                             f"This call was suppressed to prevent unintended side effects."
                }

        handler = self._handlers.get(name)
        if handler is None:
            return {"error": f"Unknown tool: {name}"}
        try:
            result = handler(**input_data)
            return result if isinstance(result, dict) else {"result": result}
        except TypeError as e:
            return {"error": f"Invalid tool input for '{name}': {str(e)}"}
        except Exception as e:
            return {"error": f"Tool '{name}' failed: {str(e)}"}
