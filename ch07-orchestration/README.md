# Chapter 7 — Multi-Agent Systems and Orchestration

Three orchestration patterns: sequential, parallel, hierarchical.

## The Coordination Tax

Before adding any agent, calculate its Coordination Tax:
- ~1–3 seconds latency per LLM hop
- Schema mismatch failure point at every handoff
- Compounded reliability: 4 agents × 95% each = 81% end-to-end

## Files

| File | Pattern | When to use |
|---|---|---|
| `sequential_pipeline.py` | Sequential | Ordered stages, each depends on previous |
| `parallel_orchestrator.py` | Parallel fan-out | Independent subtasks, need to synthesize |
| `hierarchical_orchestrator.py` | Hierarchical | Complex goals needing decomposition |
