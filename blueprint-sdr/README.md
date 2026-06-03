# Blueprint 1 — AI Sales Development Representative (SDR)

Three-agent pipeline: Lead Intelligence → Outreach Generation → Engagement Monitor.

## Files

| File | Description |
|---|---|
| `lead_intelligence.py` | Enrich a lead, score ICP fit (0–100), build research dossier |
| `outreach_sequence.py` | Generate a personalised 3-email sequence from a dossier |
| `engagement_monitor.py` | Route engagement signals: hot → human handoff, cold → follow-up |

## Architecture

```
Lead arrives (name, company, title, source)
        ▼
Lead Intelligence Agent
  ICP score < 40  → discard (log to CRM)
  ICP score 40–65 → nurture queue
  ICP score ≥ 65  → full dossier → Outreach Agent
        ▼
Outreach Generation Agent
  Enterprise → human review gate
  SMB        → auto-send sequence
        ▼
Engagement Monitor Agent
  Reply detected  → immediate human handoff package
  No reply 14d    → sequence ends; re-score in 60 days
```

## Production metrics

| Metric | Manual | With AI | Target |
|---|---|---|---|
| Research time per prospect | 45 min | 3 min | < 5 min |
| Leads per SDR day | 15–25 | 150–250 | > 100 |
| Reply rate | 2–4% | 5–10% | > 5% |

## Quick start

```bash
pip install anthropic
export ANTHROPIC_API_KEY=your_key_here
python lead_intelligence.py
```

## Hard limits

- < 50 AI-generated emails per sending domain per day
- Any reply signal → immediate human handoff (no automated reply to replies)
- Enterprise leads require human approval before sending
