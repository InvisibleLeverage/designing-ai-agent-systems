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
| `agent_test_suite.py` | Behavioral Test Suite | LLM-as-judge test runner; tests goals, not output strings |
| `agent_evaluator.py` | Agent Evaluator | Rubric-based LLM-as-judge for sampled production tasks |
| `retry_backoff.py` | Retry Backoff | Exponential backoff with jitter; decorator and functional forms |
| `task_graph.py` | Task Graph | DAG with DFS cycle detection and topological async execution |
| `confidence_routing.py` | Confidence Routing | Self-reported confidence parsing and human review queue routing |

## Key principle

> The failures that destroy production AI systems are not the ones that raise errors.
> They're the ones that don't.
