# Vector Database Comparison

For AI agent memory systems. Evaluated on: reliability, query performance, operational complexity, cost.

---

## Production Options

### Pinecone
- **Managed:** fully serverless, no infrastructure to manage
- **Performance:** sub-50ms p95 at 1M vectors
- **Pricing:** free tier (100K vectors), then $0.096/1M vectors/month
- **When to use:** production systems where operational simplicity matters
- **Limitation:** vendor lock-in, no self-hosting

### Weaviate
- **Self-hosted or managed:** available both ways
- **Strengths:** schema enforcement, hybrid search (vector + keyword), multi-tenancy
- **When to use:** when you need structured queries alongside semantic search
- **Limitation:** more operational complexity than Pinecone

### pgvector (PostgreSQL extension)
- **Self-hosted:** runs inside your existing Postgres instance
- **Strengths:** zero new infrastructure, SQL joins with metadata, ACID compliance
- **When to use:** you already run Postgres and vectors are one feature, not the core product
- **Limitation:** not designed for very high-scale pure-vector workloads

### Chroma
- **Use for:** local development and prototyping only
- **Do not use in production:** limited operational maturity, no managed offering

---

## Decision Framework

```
Already running Postgres?  →  pgvector
Need managed, low ops?     →  Pinecone
Need hybrid search?        →  Weaviate
Prototyping locally?       →  Chroma
```

---

## Embedding Models

| Model | Dimensions | Best For |
|---|---|---|
| voyage-3 (Voyage AI) | 1024 | General text, recommended for production |
| text-embedding-3-small (OpenAI) | 1536 | Cost-effective, broad language support |
| text-embedding-3-large (OpenAI) | 3072 | Higher accuracy when cost allows |

**Note:** Lock your embedding model version in production. Re-index on any model upgrade.
