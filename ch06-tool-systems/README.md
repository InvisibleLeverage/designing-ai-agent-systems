# Chapter 6 — Tool-Using AI Agents

Tool design is the most underestimated control point in agent reliability.

## Files

| File | Contract | Description |
|---|---|---|
| `tool_registry.py` | Tool Registry | Centralized tool definition and lookup |
| `tool_dispatcher.py` | Tool Dispatcher | Safe dispatch with structured error returns |
| `tool_library.py` | Tool Library | Two-layer architecture: definitions + dispatch; never raises |

## Key principle

> A tool that returns empty string on failure is a reliability bug.
> A tool that returns {"error": "rate_limited", "retry_after_ms": 2000} is a design asset.
