# Chapter 11 — The Economics of Autonomous Systems

AI agent costs scale with task complexity, not with users.

## Key insight

A multi-step pipeline that costs $2.00 to run 10 times costs $200 to run 1,000 times.
Architecture decisions (sequential vs. parallel, single vs. multi-agent) are cost decisions.

## File

| File | Contract | Description |
|---|---|---|
| `cost_guard.py` | Cost-Guarded Task Runner | Per-task cost + time budgets with automatic halting |
