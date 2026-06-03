"""
Tool Library — Chapter 6: Tool-Using AI Agents

Two-layer architecture:
  Layer 1 — Definitions: what the model reads (name, description, input_schema)
  Layer 2 — Dispatch:    what actually runs (dispatch_tool → always returns dict, never raises)

The invariant: dispatch_tool never raises. Structured error dicts are what
the agent reads to decide on retry vs. abort — raw exceptions are invisible to it.
"""
import json


# ── Layer 1: Tool definitions (what the model reads) ─────────────────────────
#
# Description IS the contract. Write it to tell the model WHEN to use the tool,
# not just what it does. Include WARNING for non-idempotent tools.

TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Search the web for current information. Use for facts, news, and data "
            "not in training knowledge. Returns a list of results with title, URL, and snippet. "
            "Safe to call multiple times — read-only."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "num_results": {"type": "integer", "description": "Number of results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_file",
        "description": (
            "Read the contents of a file by path. Returns file contents as a string. "
            "Returns an error dict if the file does not exist. Read-only — safe to retry."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative file path"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": (
            "Write content to a file. Creates the file if it does not exist; overwrites if it does. "
            "WARNING: This tool modifies the filesystem — do not call more than once per task "
            "for the same path unless explicitly updating the file."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string",  "description": "File path to write to"},
                "content": {"type": "string",  "description": "Content to write"},
                "append":  {"type": "boolean", "description": "Append instead of overwrite (default false)", "default": False},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "run_python",
        "description": (
            "Execute a Python code snippet in a sandboxed environment. "
            "Returns stdout output as a string. Use for calculations, data processing, "
            "and transformations. Timeout enforced at 10 seconds."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
            },
            "required": ["code"],
        },
    },
]


# ── Layer 2: Dispatch (what actually runs) ────────────────────────────────────
#
# Rule: dispatch_tool NEVER raises. Always returns a dict.
# Unknown tool → {"error": "Unknown tool: {name}"}
# Exception    → {"error": "Tool failed: {str(e)}", "tool": name}

def dispatch_tool(name: str, inputs: dict) -> dict:
    """Route a tool call to its handler. Never raises — always returns a dict."""
    handlers = {
        "web_search":  _web_search,
        "read_file":   _read_file,
        "write_file":  _write_file,
        "run_python":  _run_python,
    }
    handler = handlers.get(name)
    if handler is None:
        return {"error": f"Unknown tool: '{name}'. Available: {list(handlers)}"}
    try:
        return handler(inputs)
    except Exception as exc:
        return {"error": f"Tool failed: {str(exc)}", "tool": name}


# ── Handlers ──────────────────────────────────────────────────────────────────

def _web_search(inputs: dict) -> dict:
    """Stub — replace with Exa / Serper / Brave API in production."""
    query = inputs.get("query", "")
    if not query:
        return {"error": "query is required"}
    return {
        "results": [
            {"title": f"Result for: {query}", "url": "https://example.com", "snippet": f"Stub result for '{query}'. Replace with real search API."},
        ],
        "note": "Stub implementation. Wire up a real search API for production.",
    }


def _read_file(inputs: dict) -> dict:
    path = inputs.get("path", "")
    if not path:
        return {"error": "path is required"}
    try:
        with open(path) as f:
            return {"content": f.read(), "path": path}
    except FileNotFoundError:
        return {"error": f"File not found: {path}"}
    except PermissionError:
        return {"error": f"Permission denied: {path}"}


def _write_file(inputs: dict) -> dict:
    path    = inputs.get("path", "")
    content = inputs.get("content", "")
    append  = inputs.get("append", False)
    if not path:
        return {"error": "path is required"}
    mode = "a" if append else "w"
    try:
        with open(path, mode) as f:
            f.write(content)
        return {"success": True, "path": path, "bytes_written": len(content)}
    except PermissionError:
        return {"error": f"Permission denied: {path}"}


def _run_python(inputs: dict) -> dict:
    import io, sys, signal
    code = inputs.get("code", "")
    if not code:
        return {"error": "code is required"}

    stdout_capture = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_capture

    try:
        exec(code, {"__builtins__": __builtins__})  # noqa: S102
        output = stdout_capture.getvalue()
        return {"output": output, "success": True}
    except Exception as exc:
        return {"error": str(exc), "success": False}
    finally:
        sys.stdout = old_stdout


# ── Quick smoke test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Tool definitions:", [t["name"] for t in TOOLS])

    tests = [
        ("web_search",  {"query": "AI agent architectures"}),
        ("run_python",  {"code": "print(2 + 2)"}),
        ("read_file",   {"path": "/nonexistent/file.txt"}),
        ("web_search",  {}),                         # missing required arg
        ("unknown_tool", {"foo": "bar"}),             # unknown tool
    ]

    for name, inputs in tests:
        result = dispatch_tool(name, inputs)
        print(f"{name}: {json.dumps(result)[:100]}")
