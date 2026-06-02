# Chapter 8 — Deployment and Scaling

Production infrastructure for AI agent systems: async task queues, cost controls, token budgets, and model routing.

## Files

| File | Contract | Description |
|---|---|---|
| `fastapi_agent_service.py` | Agent Service | Async FastAPI service wrapping the agent loop with task lifecycle management |
| `cost_manager.py` | Cost Manager | Per-user and system-wide API cost tracking with daily budget enforcement |
| `token_budget_manager.py` | Token Budget | Per-category context window allocation to prevent runaway token loops |
| `model_router.py` | Model Router | Route tasks to Haiku / Sonnet / Opus by complexity to cut costs 60–80% |

## Key principle

> Scaling agents is mostly a queueing problem. The model API is already horizontally
> scalable — the provider handles that. Your scaling work is the queue architecture
> that feeds it: stateless workers, priority lanes, and dead-letter queues that catch
> failures before they evaporate.

## Quick start

```bash
pip install fastapi uvicorn anthropic
uvicorn fastapi_agent_service:app --reload
```

Set your API key first:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

Submit a task:

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"goal": "Summarise the main risks of transformer architectures", "user_id": "u1"}'
```

Poll for result using the returned `task_id`.
