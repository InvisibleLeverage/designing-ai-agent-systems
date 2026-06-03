# Blueprint 5 — Enterprise Sales Automation System

Qualify → research → personalised outreach → nurture cadence. Reduces time-to-first-outreach from 2–4 days to under 4 hours.

## Files

| File | Description |
|---|---|
| `enterprise_sales.py` | Full pipeline: lead qualification, dossier research, outreach generation, nurture cadence |

## Architecture

```
Inbound lead signal
        ▼
Qualification Agent (Sonnet)
  Score 1–10 vs ICP criteria
  High (≥7) → Research Agent
  Nurture (4–6) → light 2-touch sequence
  Discard (<4) → log reason + stop
        ▼ (high tier only)
Research Agent (Opus)
  Dossier: pain points, triggers, decision map
  Missing data → explicit gap; never invented
        ▼
Outreach Agent (Sonnet)
  3-sentence personalised email
  1 specific verifiable fact, 0 adjectives, CTA with time
  Enterprise → human review gate
        ▼
Nurture Agent (Haiku)
  Follow-up cadence: Days 5, 12
  Reply detected → immediate human rep handoff
```

## Production metrics

| Metric | Manual | With AI | Target |
|---|---|---|---|
| Time to first outreach | 2–4 days | < 4 hours | < 8 hours |
| Leads per SDR day | 15–25 | 150–250 | > 100 |
| Response rate | 2–4% | 6–12% | > 5% |
| Cost per qualified meeting | $400–800 | $80–160 | < $200 |

## Quick start

```bash
pip install -r requirements.txt
export AI_API_KEY=your_key_here
python enterprise_sales.py
```
