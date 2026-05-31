# Chapter 3 — Designing AI Agent Architectures

Implementation contracts for the four-layer agent architecture.

## Files

| File | Contract | Description |
|---|---|---|
| `goal_parser.py` | Goal Parser | Parses raw user goals into structured subtasks |
| `agent_loop.py` | Agent Loop | Core perception-reasoning-action loop |
| `tool_library.py` | Tool Library | Tool definition and dispatch layer |
| `parallel_fanout.py` | Parallel Fan-out | Concurrent subtask execution |

## Key principle

> Architecture determines what the agent can do. The four layers — goal interface,
> reasoning engine, memory, tool boundary — are load-bearing decisions.
> Getting them right is cheaper than redesigning them under load.

## Quick start

```bash
python agent_loop.py
```

Requires `ANTHROPIC_API_KEY` in environment.
