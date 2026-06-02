# Chapter 14 — AI Business Automation Systems

CRM intelligence, proposal generation, and automation selection framework for high-ROI business workflows.

## Files

| File | Contract | Description |
|---|---|---|
| `crm_intelligence.py` | CRM Intelligence | Analyse contacts, surface at-risk accounts, draft personalised follow-ups |
| `proposal_generator.py` | Proposal Generator | Generate structured proposals from a project brief in ~5 minutes |

## Key principle

> The highest-ROI business automations are not the most complex — they are the ones
> where the cost of human time is highest and the quality bar is clearest.
> Map cost of human time first; technical complexity is secondary.

## Automation selection scoring

Score your workflow candidate on these five factors (1–5 each):

| Factor | Why it matters |
|---|---|
| Human time cost per run | Higher cost → higher ROI on automation |
| Run frequency per week | More frequent → faster payback |
| Quality bar clarity | Clear bar → easier to validate AI output |
| Error reversibility | Reversible errors → lower production risk |
| Data availability | More existing data → faster to calibrate |

**Decision:** 20–25 = build now; 14–19 = build with HITL; < 14 = prototype only.

## Quick start

```bash
pip install anthropic
python crm_intelligence.py    # analyses sample contacts and drafts follow-ups
python proposal_generator.py  # generates a sample proposal from a brief
```

Set your API key first:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

## Important

AI-generated proposals and outreach drafts need a human review gate before sending.
Use these tools to reach a 90% draft fast; the reviewer adds the judgment the AI cannot:
unstated political dynamics, budget sensitivities, competitive nuance.
