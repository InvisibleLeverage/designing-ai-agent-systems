# Blueprint 2 — Autonomous Research Pipeline

Decompose → parallel specialist agents → synthesize → verification flags. Delivers a research brief in 8–12 minutes vs 4–8 hours for a human analyst.

## Files

| File | Description |
|---|---|
| `research_pipeline.py` | Full pipeline: decompose brief → parallel agents → synthesis → verification flags |

## Architecture

```
Research brief (natural language)
        ▼
Decomposition Agent (Opus)
  Parses → typed parallel subtasks + source plan
        ▼ (asyncio.gather — all parallel)
┌──────────────┬──────────────┬─────────────────┐
│Company       │Industry      │Competitive      │
│Profiler      │Analyst       │Intelligence     │
│(Sonnet)      │(Sonnet)      │(Sonnet)         │
└──────────────┴──────────────┴─────────────────┘
        ▼
Synthesis Agent (Opus)
  Merges + resolves contradictions
        ▼
Verification Flag Agent (Haiku)
  Flags numbers, recent events, legal claims
        ▼
Deliverable: report + verification checklist
```

## Agent roles

| Agent | Model | Escalation |
|---|---|---|
| Decomposition | Opus | Ambiguous brief → clarification request |
| Company Profiler | Sonnet | Missing data → explicit gap flag |
| Industry Analyst | Sonnet | Conflicting signals → surface both |
| Competitive Intelligence | Sonnet | Insufficient data → flag; never invent |
| Synthesis | Opus | < 60% confidence → surface gaps |
| Verification Flag | Haiku | Always runs; never skipped |

## Quick start

```bash
pip install anthropic
export ANTHROPIC_API_KEY=your_key_here
python research_pipeline.py
```
