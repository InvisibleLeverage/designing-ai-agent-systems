# Memory Schema Template

Use this to define what your agent stores, where, and for how long.

## Four-Layer Decision Matrix

| Information Type | Layer | TTL | Eviction Rule |
|---|---|---|---|
| Current task state, tool outputs | In-context working memory | Task session | End of task |
| User preferences, session context | Session storage | 24 hours | Session end |
| Domain knowledge, past outcomes | Vector store | 90 days | LRU + staleness |
| User profiles, structured facts | Relational (SQL) | Indefinite | Never (manual) |

## What NOT to Store

- Raw tool outputs (store extracted facts, not raw HTML)
- Intermediate reasoning steps (store conclusions, not scratchpad)
- Model-generated inferences without source attribution
- High-uncertainty outputs (confidence < 0.7)

## Write Policy

```python
# Write-time validation before any memory persistence
WRITE_POLICY = {
    "min_confidence":      0.7,      # reject below this threshold
    "require_source":      True,     # every write must have a source attribution
    "max_staleness_hours": 24.0,     # trigger warning after this age
    "validate_schema":     True,     # validate against field schema before write
}
```

## Retrieval Policy

```python
RETRIEVAL_POLICY = {
    "similarity_threshold": 0.75,   # minimum cosine similarity
    "max_results":          5,       # cap results to control context budget
    "recency_weight":       0.2,     # blend similarity with recency (0 = pure similarity)
    "exclude_stale":        False,   # if True, filter entries older than staleness threshold
}
```
