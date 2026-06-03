# Blueprint 3 — AI Content Studio

Brief → research + keyword strategy → parallel section drafting → edit → channel variants. Reduces long-form content production from 8–12 hours to 40–60 minutes.

## Files

| File | Description |
|---|---|
| `content_studio.py` | Full pipeline: research, outline, parallel writing, editing, channel adaptation |

## Architecture

```
Editorial brief (topic + audience + goal)
        ▼ (parallel)
┌──────────────┬──────────────────┐
│Research      │Keyword Strategy  │
│Agent(Sonnet) │Agent (Haiku)     │
└──────────────┴──────────────────┘
        ▼
Content Architect (Sonnet) — outline + SEO structure
        ▼ (asyncio.gather — all sections parallel)
Section Writers × N (Opus, 600 tokens/section max)
        ▼
Editor Agent (Sonnet) — voice + flow + quality gate
        ▼ (asyncio.gather — all channels parallel)
┌────────────┬──────────┬─────────┬──────────┐
│LinkedIn    │Twitter   │Email    │Meta/Ad   │
│(Haiku)     │(Haiku)   │(Haiku)  │(Haiku)   │
└────────────┴──────────┴─────────┴──────────┘
```

## Production metrics

| Metric | Manual | With AI | Target |
|---|---|---|---|
| Time: long-form + variants | 8–12 hours | 40–60 min | < 60 min |
| Articles per editor/week | 2–3 | 6–10 | > 6 |
| Channel variants per article | 1–2 | 4–6 | All major channels |

## Quick start

```bash
pip install -r requirements.txt
export AI_API_KEY=your_key_here
python content_studio.py
```

## Important

Always include a human review gate before publishing.
The pipeline produces a 90% draft — human editorial judgment handles the final 10%.
