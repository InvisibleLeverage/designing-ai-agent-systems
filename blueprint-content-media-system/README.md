# Blueprint 7 — AI Content & Media System

Full content pipeline with a performance feedback loop. Content strategy improves with volume — each published piece updates Topic Intelligence scores that drive the next brief.

## Files

| File | Description |
|---|---|
| `content_media_system.py` | Pipeline + Topic Intelligence store + performance feedback loop |

## What differentiates this from Blueprint 3

| Feature | Blueprint 3 (studio) | Blueprint 7 (media system) |
|---|---|---|
| Topic selection | Editorial judgment only | Data-driven angle scoring |
| Performance feedback | None | Weekly automated update |
| Audience modeling | Static brief | Evolves with engagement data |
| Content strategy | Manual | Compounds with volume |

## Architecture

```
Weekly: Performance Tracker updates Topic Intelligence store
        ▼ (triggered by editorial brief)
Topic Intelligence query → recommended topics + angle scores
        ▼
Research + Outline (parallel, Sonnet)
        ▼
Section Writers × N (Opus, parallel, 600 tokens/section)
        ▼
Editor (Sonnet) — voice + quality gate
        ▼
Distribution Adapters × 4 (Haiku, parallel)
        ▼
Publish → analytics integration → feedback into Topic Intelligence
```

## Engagement scoring formula

```
score = clicks×1 + shares×3 + replies×2 + saves×4
```

After 8–12 weeks, content strategy is grounded in actual audience behaviour.

## Quick start

```bash
pip install -r requirements.txt
export AI_API_KEY=your_key_here
python content_media_system.py
```

## Important

- Human review gate required before publishing
- Diversity constraint: no single topic > 30% of monthly output (prevents monoculture)
- Recalibrate voice spec every 20 published pieces to prevent drift
