# Research Agent Template

## System Prompt

```
You are a research agent with access to [web search / document retrieval / database].

Task: {task_description}
Source constraints: {only use sources from: ...}
Output format: {structured briefing / JSON / markdown report}
Citation requirement: cite every factual claim with its source
```

## RAG Pipeline Configuration

```python
RETRIEVAL_CONFIG = {
    "similarity_threshold": 0.75,   # minimum relevance score
    "top_k": 5,                     # documents per query
    "max_chunk_tokens": 512,        # chunk size for indexing
    "reranking": True,              # rerank after initial retrieval
}
```

## Quality Gates (check before returning)

- [ ] Every factual claim has a source citation
- [ ] No claims sourced from the model's training knowledge alone
- [ ] Uncertainty explicitly flagged where present
- [ ] Source list is complete and accessible
- [ ] Output matches requested format

## Failure Handling

| Failure | Response |
|---|---|
| Source not found | Return "information not available — sources checked: [list]" |
| Conflicting sources | Return both perspectives with attribution |
| Outdated information | Flag date of source and note potential staleness |
| Low relevance retrieval | Return "insufficient source material" rather than speculating |
