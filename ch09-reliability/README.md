# Chapter 9 — System Reliability and Safety

Production reliability patterns. These are not optional — they are the deployment.

## Files

| File | Contract | Description |
|---|---|---|
| `circuit_breaker.py` | Circuit Breaker | Fail-fast on degraded dependencies |
| `output_validator.py` | Output Validation | LLM-as-judge grounding checks |
| `loop_detector.py` | Loop Detector | Detect and halt infinite agent loops |
| `validated_memory_store.py` | Validated Memory | Confidence-gated write + stale-read detection |
| `agent_handoff_validation.py` | Handoff Validation | Schema check at every inter-agent boundary |

## Key principle

> The failures that destroy production AI systems are not the ones that raise errors.
> They're the ones that don't.
