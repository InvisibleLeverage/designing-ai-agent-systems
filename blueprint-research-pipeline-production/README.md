# Blueprint 6 — Production Research Agent Pipeline

Enterprise-grade research pipeline with source caching, semantic memory, per-claim confidence scores, and cost controls. Builds on Blueprint 2 — adds the production infrastructure that makes research scale without compounding costs.

## Files

| File | Description |
|---|---|
| `production_research.py` | Full pipeline: memory check → source cache → parallel agents → synthesis → quality check → memory store |

## What differentiates production from prototype

| Feature | Blueprint 2 (prototype) | Blueprint 6 (production) |
|---|---|---|
| Prior research reuse | No | Semantic similarity check; supplement if ≥ 70% overlap |
| Source caching | No | Redis 24h TTL — no re-fetching identical URLs |
| Cost controls | No | Per-task budget cap; alert on overrun |
| Confidence scores | Summary only | Per-claim confidence in synthesis |
| Memory | No | Stores reports for future overlap detection |

## Architecture

```
Research brief
        ▼
Memory check (semantic similarity ≥ 70%?)
  Yes → supplement from prior (delta subtasks only)
  No  → full decompose → task plan
        ▼
Source cache check (24h TTL)
  Hit  → return cached content
  Miss → fetch, parse, cache
        ▼ (asyncio.gather)
Web Search + Document Reader + Database Query (parallel)
        ▼
Synthesis Agent (Opus) — report + per-claim confidence
        ▼
Quality Check Agent (Haiku) — gaps + verification flags
        ▼
Store in memory → deliver report + checklist
```

## Quick start

```bash
pip install anthropic
export ANTHROPIC_API_KEY=your_key_here
python production_research.py
```

Replace stub `SourceCache` with Redis and stub `ResearchMemory` with Pinecone/Weaviate for production.
