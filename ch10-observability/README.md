# Chapter 10 — System Observability and Operational Intelligence

Instrumentation for AI agent systems: distributed tracing, quality signals, retrieval drift detection, and cost telemetry.

## Files

| File | Contract | Description |
|---|---|---|
| `agent_tracer.py` | Agent Tracer | Structured telemetry events — one per agent step, correlated by task_id |
| `quality_monitor.py` | Quality Monitor | Confidence tracking, schema compliance rate, hallucination detection signals |
| `retrieval_health.py` | Retrieval Health | Similarity score distribution tracking, retrieval drift detection |

## Key principle

> Reliability prevents failures. Observability reveals them.
> A monitoring system that shows green while your agent confidently produces wrong
> answers is not observing your system — it is observing its infrastructure.
> Layers 2 and 3 (behavioural and quality signals) are where production reliability lives.

## The five metrics that actually matter

| Metric | What it catches | Alert threshold |
|---|---|---|
| Task pass rate (rolling 7d) | Silent Degradation | Drop > 5pp vs prior week |
| Step-limit termination rate | Agent getting stuck | > 3% of tasks |
| P95 cost per task | Runaway token loops | > 2× baseline |
| Tool error rate | Tool degradation | > 5% for any tool |
| Retrieval utilisation | Context flooding / poor RAG | < 40% of retrieved chunks used |

## Quick start

```bash
python agent_tracer.py       # emits sample trace events to stdout
python quality_monitor.py    # runs a sample quality check
python retrieval_health.py   # prints a sample drift report
```
