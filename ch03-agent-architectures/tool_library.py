"""
Tool Library + Dispatcher — Chapter 3: Designing AI Agent Architectures

The tool library is the only interface the model sees.
Every description must answer: WHEN to use this, WHAT the output looks like,
WARNING if non-idempotent.

Contract: dispatch_tool(name, input) → dict  (NEVER raises — always returns a dict)
"""
import json
import os
from datetime import datetime

import anthropic


def _search_web(query: str) -> dict:
    """Stub — replace with a real search API (Brave, Serper, etc.)."""
    return {"results": [f"[stub] Result for: {query}"], "query": query}


def _read_file(path: str) -> dict:
    try:
        with open(path) as f:
            return {"content": f.read(), "path": path}
    except FileNotFoundError:
        return {"error": f"File not found: {path}"}
    except Exception as e:
        return {"error": str(e)}


def _get_current_time() -> dict:
    return {"time": datetime.utcnow().isoformat() + "Z"}


# ── Tool definitions (what the model reads) ────────────────────────────────────

TOOLS = [
    {
        "name": "search_web",
        "description": (
            "Search the web for current information. Use when you need facts, "
            "recent events, or information not available in your training. "
            "Returns a list of relevant text snippets. "
            "WARNING: results may be outdated or inaccurate — verify critical claims."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_file",
        "description": (
            "Read the contents of a local file. Use when the user references a file "
            "by path, or when you need to read previously written output. "
            "Returns {content: string} on success or {error: string} on failure."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative file path"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "get_current_time",
        "description": (
            "Returns the current UTC time in ISO 8601 format. "
            "Use when the task requires knowing the current date or time."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


# ── Dispatcher (what actually runs) ───────────────────────────────────────────

_HANDLERS = {
    "search_web":       lambda inp: _search_web(inp["query"]),
    "read_file":        lambda inp: _read_file(inp["path"]),
    "get_current_time": lambda inp: _get_current_time(),
}


def dispatch_tool(name: str, input_data: dict) -> dict:
    """
    Dispatch a tool call. NEVER raises — always returns a dict.
    Unknown tool or exception → structured error dict.
    """
    handler = _HANDLERS.get(name)
    if handler is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return handler(input_data)
    except Exception as e:
        return {"error": f"Tool failed: {str(e)}", "tool": name}
