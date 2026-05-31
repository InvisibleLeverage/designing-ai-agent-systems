# Recommended Tools for AI Agent Systems

Tools evaluated for production suitability across the agent stack.

---

## Model APIs

| Provider | Models | Best For |
|---|---|---|
| Anthropic | Claude Sonnet 4.6, Haiku 4.5, Opus 4.8 | Production agents, complex reasoning, tool use |
| OpenAI | GPT-4o, GPT-4o-mini | Broad ecosystem, function calling |
| Google | Gemini 1.5 Pro | Long-context tasks, multimodal |

**Recommendation:** Claude Sonnet 4.6 for production agents. Haiku 4.5 for validation
and classification subtasks where cost matters. Opus 4.8 for high-stakes single-call tasks.

---

## Vector Databases

| Tool | Best For | Self-Hosted |
|---|---|---|
| Pinecone | Managed, serverless, fast | No |
| Weaviate | Schema enforcement, hybrid search | Yes |
| pgvector | Existing Postgres stack | Yes |
| Chroma | Local dev, prototyping | Yes |

**Recommendation:** pgvector if you already have Postgres. Pinecone for managed production.
Chroma for local development only — do not use in production.

---

## Observability

| Tool | Best For |
|---|---|
| Langfuse | AI-specific tracing, prompt versioning, cost tracking |
| Helicone | Lightweight API proxy logging |
| Datadog | Existing infrastructure integration |
| Prometheus + Grafana | Self-hosted metrics and dashboards |

**Recommendation:** Langfuse for AI-specific observability. Add Prometheus for infrastructure metrics.

---

## Task Queues

| Tool | Best For |
|---|---|
| Redis + RQ | Simple, fast, Python-native |
| Celery | Complex workflows, multiple brokers |
| CloudWatch Events | AWS-native, scheduled tasks |

---

## Development

| Tool | Purpose |
|---|---|
| `python-dotenv` | Environment variable management |
| `pytest` | Testing framework |
| `httpx` | Async HTTP client for tool implementations |
