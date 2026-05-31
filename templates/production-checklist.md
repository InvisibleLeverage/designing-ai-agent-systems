# Production Launch Checklist

Based on Chapter 9: System Reliability and Safety

---

## Before You Ship

### Instrumentation (non-negotiable)
- [ ] One structured log record per agent step: task_id, tool, success, tokens, duration_ms
- [ ] Per-task cost tracking (not daily aggregate — per task)
- [ ] Step count monitoring with alert threshold
- [ ] Tool error rate per tool name (primary reliability signal)

### Reliability Contracts
- [ ] Every tool returns `{"error": "..."}` on failure — never empty string
- [ ] Every tool description states WHEN to use it and WARNING if non-idempotent
- [ ] Circuit breaker on every external dependency
- [ ] Step limit configured and tested (what happens at step 20?)

### Degraded Mode
- [ ] What does the system return when the model API is unavailable?
- [ ] What does it return when a critical tool fails?
- [ ] Is the degraded response useful, or just an error?

### Validation
- [ ] Output schema validation on agent responses
- [ ] Confidence threshold defined for autonomous action
- [ ] Human escalation path for below-threshold outputs

---

## Launch Blocked If

- [ ] No structured logging in place
- [ ] Any tool returns empty string on failure
- [ ] No step limit configured
- [ ] No cost alerting at per-task level
- [ ] Failure mode produces confusing or harmful output

---

## Post-Launch Monitoring (first 72 hours)

- [ ] Check per-task cost distribution daily
- [ ] Review tool error rate by tool name
- [ ] Sample 5–10 outputs manually per day
- [ ] Monitor step count distribution for anomalies
- [ ] Verify escalation path is actually routing correctly
