# Chapter 12 — AI Research and Knowledge Agents

RAG pipelines and multi-document intelligence for grounded, traceable research.

## Files

| File | Contract | Description |
|---|---|---|
| `rag_research_system.py` | RAG Research System | Three-stage pipeline: chunk → embed+index → retrieve → grounded generation |
| `document_intelligence.py` | Document Intelligence | Three-pass multi-document analysis: per-doc → synthesis → structured extraction |

## Key principle

> The core value of RAG is not that it gives the model more information — it is that
> it gives the model *verifiable* information. Every claim can be traced to a source.
> Grounding is the engineering problem in AI research, not generation.

## Quick start

```bash
pip install -r requirements.txt
python rag_research_system.py   # indexes sample docs and answers a question
python document_intelligence.py # runs three-pass analysis on sample documents
```

Set your API key first:

```bash
export AI_API_KEY=your_key_here
```

## Architecture

```
RAG PIPELINE

[Query] → [Retrieval System]  → [Retrieved Chunks]
                                        ↓
                               [Context Construction]
                                        ↓
                               [Language Model] → [Response + Sources]
```

Replace the keyword-score retrieval stub in `rag_research_system.py` with real
embeddings (`text-embedding-3-small`, Cohere `embed-v3`, or Voyage) and a vector
store (Pinecone, pgvector, Weaviate) for production use.
