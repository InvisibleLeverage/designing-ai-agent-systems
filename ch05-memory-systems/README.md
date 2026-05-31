# Chapter 5 — Memory Systems and Context Management

The four-layer memory architecture: in-context, session, vector, relational.

## Files

| File | Contract | Description |
|---|---|---|
| `context_manager.py` | Context Manager | Budget-aware context assembly |
| `session_memory.py` | Session Memory | Short-term per-task state |
| `vector_memory.py` | Vector Memory | Semantic long-term retrieval |

## Key principle

> Context quality determines output quality.
> The model's reasoning is not the bottleneck — what it has access to is.
