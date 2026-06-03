# Blueprint 4 — AI Finance Analyst System

Earnings transcript → structured metrics → beat/miss analysis → risk identification. Produces first-pass analysis in minutes; always requires human analyst review before distribution.

## Files

| File | Description |
|---|---|
| `finance_analyst.py` | Full pipeline: parse transcript → analyse earnings → identify risks → human review gate |

## Architecture

```
Earnings input (transcript + estimates + prior guidance)
        ▼
Transcript Parser (Sonnet)
  Extract: metrics, quotes, guidance
  Normalize: YoY/QoQ conventions
  Missing figures → explicit null + flag
        ▼
Earnings Analyst (Opus)
  Compare: actuals vs estimates
  Assess: guidance + management tone
  Flag: absent or uncertain figures — never interpolate
        ▼
Risk Identifier (Opus)
  Bull case / bear case articulation
  Analyst question suggestions
        ▼
HUMAN ANALYST REVIEW GATE (always required)
  Disclaimer auto-appended to all output
```

## Regulatory note

In most jurisdictions, AI-generated financial analysis must be clearly labelled and reviewed by a qualified professional before acting on it. The review gate and disclaimer are **architectural components**, not optional.

## Quick start

```bash
pip install -r requirements.txt
export AI_API_KEY=your_key_here
python finance_analyst.py
```
