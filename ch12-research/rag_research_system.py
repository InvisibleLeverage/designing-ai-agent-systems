"""
RAG Research System — Chapter 12: AI Research and Knowledge Agents

Three-stage pipeline: chunk → embed+index → retrieve → grounded generation.

Production swap-ins:
  - Replace keyword scoring with cosine similarity over real embeddings
    (text-embedding-3-small, Cohere embed-v3, or Voyage)
  - Replace in-memory store with Pinecone / pgvector / Weaviate
"""
import os
import re
import textwrap
from dataclasses import dataclass, field
from typing import Optional

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))
MODEL = "claude-sonnet-4-6"

CHUNK_SIZE    = 500    # words per chunk
CHUNK_OVERLAP = 50     # words of overlap between adjacent chunks
TOP_K         = 5      # chunks retrieved per query
SIM_THRESHOLD = 0.10   # minimum relevance score (keyword heuristic; use ~0.65 for cosine)


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class Chunk:
    chunk_id:  int
    content:   str
    metadata:  dict = field(default_factory=dict)


@dataclass
class RetrievedChunk:
    chunk:           Chunk
    relevance_score: float


# ── RAG Research System ───────────────────────────────────────────────────────

class RAGResearchSystem:
    def __init__(self):
        self._store: list[Chunk] = []
        self._next_id = 0

    # ── Indexing ─────────────────────────────────────────────────────────────

    def add_document(self, text: str, metadata: Optional[dict] = None) -> int:
        """Chunk document and store. Returns number of chunks indexed."""
        chunks = self._chunk_text(text)
        for chunk_text in chunks:
            self._store.append(Chunk(
                chunk_id=self._next_id,
                content=chunk_text,
                metadata=metadata or {},
            ))
            self._next_id += 1
        return len(chunks)

    # ── Retrieval ────────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[RetrievedChunk]:
        """
        Retrieve the most relevant chunks for a query.

        Stub: keyword overlap scoring.
        Production: replace with embedding cosine similarity.
        """
        query_terms = set(re.sub(r'[^\w\s]', '', query.lower()).split())
        scored: list[tuple[float, Chunk]] = []

        for chunk in self._store:
            chunk_terms = set(re.sub(r'[^\w\s]', '', chunk.content.lower()).split())
            overlap = len(query_terms & chunk_terms)
            score   = overlap / max(len(query_terms), 1)
            if score >= SIM_THRESHOLD:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            RetrievedChunk(chunk=c, relevance_score=round(s, 4))
            for s, c in scored[:top_k]
        ]

    # ── Grounded generation ───────────────────────────────────────────────────

    def answer(self, question: str) -> dict:
        """
        Retrieve relevant chunks, then generate a grounded answer.
        Returns: {answer, sources, chunks_used, confidence}.
        """
        retrieved = self.retrieve(question)
        if not retrieved:
            return {
                "answer":      "No relevant documents found in the knowledge base.",
                "sources":     [],
                "chunks_used": 0,
                "confidence":  "LOW",
            }

        context_blocks = []
        source_ids     = []
        for i, rc in enumerate(retrieved, start=1):
            label = rc.chunk.metadata.get("source", f"Chunk {rc.chunk.chunk_id}")
            context_blocks.append(f"[SOURCE {i}: {label}]\n{rc.chunk.content}")
            source_ids.append(label)

        context = "\n\n".join(context_blocks)
        prompt  = (
            f"Answer the question using ONLY the provided sources below. "
            f"Quote relevant passages to support your answer. "
            f"If the sources do not contain enough information, say so explicitly. "
            f"At the end, rate your confidence: HIGH, MEDIUM, or LOW.\n\n"
            f"SOURCES:\n{context}\n\n"
            f"QUESTION: {question}"
        )

        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        answer_text = response.content[0].text
        confidence  = self._extract_confidence(answer_text)

        return {
            "answer":      answer_text,
            "sources":     list(dict.fromkeys(source_ids)),   # deduplicated, ordered
            "chunks_used": len(retrieved),
            "confidence":  confidence,
        }

    # ── Internals ────────────────────────────────────────────────────────────

    @staticmethod
    def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
        words  = text.split()
        chunks = []
        start  = 0
        while start < len(words):
            end = start + size
            chunks.append(" ".join(words[start:end]))
            start += size - overlap
        return [c for c in chunks if c.strip()]

    @staticmethod
    def _extract_confidence(text: str) -> str:
        for level in ("HIGH", "MEDIUM", "LOW"):
            if level in text.upper():
                return level
        return "MEDIUM"


# ── Quick smoke test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    system = RAGResearchSystem()

    system.add_document(
        "Transformer models use self-attention mechanisms to process sequences in parallel. "
        "The attention mechanism allows each token to attend to all other tokens in the sequence, "
        "enabling the model to capture long-range dependencies. Multi-head attention runs "
        "several attention functions in parallel and concatenates their outputs.",
        metadata={"source": "attention_paper.pdf", "page": 3},
    )
    system.add_document(
        "Large language models are trained on vast corpora using next-token prediction. "
        "Scale improves performance across a wide range of tasks, a phenomenon known as "
        "emergent abilities. Models with over 100B parameters exhibit qualitatively "
        "different capabilities than smaller models.",
        metadata={"source": "scaling_laws.pdf", "page": 1},
    )
    system.add_document(
        "Agent systems extend language models with tool use and memory. "
        "The agent loop: receive goal → plan → act → observe → evaluate. "
        "Reliability failures occur at boundaries between components, not at the reasoning layer.",
        metadata={"source": "designing_ai_agents.pdf", "page": 15},
    )

    result = system.answer("How do transformer attention mechanisms work?")
    print(f"Answer:\n{textwrap.fill(result['answer'][:500], 80)}\n")
    print(f"Sources:    {result['sources']}")
    print(f"Chunks used: {result['chunks_used']}")
    print(f"Confidence:  {result['confidence']}")
