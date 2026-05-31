# Deployment Runbook — AI Agent System

---

## On-Call Quick Reference

**System:** [Agent System Name]
**Owner:** [Team/Person]
**Dashboard:** [URL]
**Escalation:** [Slack channel / PagerDuty]

---

## Severity Classification

| Level | Description | Response Time |
|---|---|---|
| SEV-1 | System down or producing harmful outputs | 15 minutes |
| SEV-2 | Degraded quality, elevated error rate | 1 hour |
| SEV-3 | Non-critical anomaly, trending concern | Next business day |

---

## Common Incidents

### Cost Spike (> 2× baseline)
1. Check per-task cost in dashboard — identify outlier task types
2. Check step count distribution — is an agent looping?
3. Check tool call volume — which tool is being called excessively?
4. If runaway loop: disable the affected agent type, not the whole system

### Quality Degradation (user reports, quality score drop)
1. Check embedding model version — did the provider update?
2. Check retrieval similarity scores — are they lower than baseline?
3. Sample 20 recent outputs manually
4. If retrieval degraded: re-index; do not tune prompts until retrieval is verified

### Tool Failure Rate Spike
1. Check tool error rate by tool name in dashboard
2. Test the affected tool in isolation
3. Check if the external API/service the tool depends on is degraded
4. Activate circuit breaker if error rate > 20% for > 5 minutes

---

## Rollback Procedure
1. Identify the deployment that introduced the regression (use deployment timestamps)
2. Revert the prompt/config change (prefer config rollback over code rollback)
3. Verify baseline metrics return within 15 minutes
4. File incident report within 24 hours

---

## Escalation Matrix

| Trigger | Escalate To |
|---|---|
| SEV-1 open > 30 minutes | Engineering lead + Product |
| Cost spike > 5× baseline | Engineering lead + Finance |
| Data privacy concern | Legal + Engineering lead immediately |
| Harmful output delivered to user | Product + Legal immediately |
