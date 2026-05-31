"""
Tool Registry — Chapter 6: Tool-Using AI Agents

Centralized registry for tool definitions.
Separates what the model sees (descriptions) from what actually runs (handlers).
"""
import functools
from typing import Callable


class ToolRegistry:
    """Maintains the tool library and dispatches calls."""

    def __init__(self):
        self._definitions: list[dict] = []
        self._handlers: dict[str, Callable] = {}

    def register(self, definition: dict, handler: Callable) -> None:
        """Register a tool with its Anthropic-format definition and a handler."""
        name = definition["name"]
        self._definitions.append(definition)
        self._handlers[name] = handler

    def tool(self, name: str, description: str, input_schema: dict):
        """Decorator for registering a tool inline."""
        def decorator(fn: Callable) -> Callable:
            self.register(
                {"name": name, "description": description, "input_schema": input_schema},
                fn,
            )
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    @property
    def definitions(self) -> list[dict]:
        """Tool definitions for passing to the model API."""
        return self._definitions

    def dispatch(self, name: str, input_data: dict) -> dict:
        """Dispatch a tool call. NEVER raises — always returns a dict."""
        handler = self._handlers.get(name)
        if handler is None:
            return {"error": f"Unknown tool: {name}"}
        try:
            result = handler(**input_data)
            return result if isinstance(result, dict) else {"result": result}
        except Exception as e:
            return {"error": f"Tool failed: {str(e)}", "tool": name}


# Example registry
registry = ToolRegistry()


@registry.tool(
    name="calculate",
    description="Perform arithmetic calculations. Returns the numeric result. Use for any math.",
    input_schema={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "A valid Python arithmetic expression, e.g. '(42 * 1.15) / 2'",
            }
        },
        "required": ["expression"],
    },
)
def calculate(expression: str) -> dict:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return {"error": "Invalid expression: only arithmetic operators allowed"}
    try:
        return {"result": eval(expression)}  # noqa: S307 — arithmetic only, validated above
    except Exception as e:
        return {"error": str(e)}
