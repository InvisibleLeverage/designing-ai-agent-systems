"""
Document Intelligence Pipeline — Chapter 12: AI Research and Knowledge Agents

Three-pass multi-document analysis:
  Pass 1 (parallel): Per-document analysis — summary, key findings, limitations
  Pass 2 (sequential): Cross-document synthesis — themes, agreements, conflicts
  Pass 3 (structured): Extraction — JSON structured output for downstream use

Route only the top-ranked documents through all three passes to control cost.
"""
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL  = "claude-sonnet-4-6"


@dataclass
class DocumentAnalysis:
    index:       int
    source:      str
    summary:     str
    findings:    list[str]
    limitations: list[str]
    relevance:   str   # HIGH | MEDIUM | LOW


@dataclass
class IntelligenceReport:
    synthesis:        str
    key_themes:       list[str]
    agreements:       list[str]
    conflicts:        list[str]
    extracted:        dict
    documents_used:   int
    total_documents:  int


def _analyse_document(index: int, text: str, goal: str) -> DocumentAnalysis:
    """Pass 1: analyse a single document in the context of the research goal."""
    prompt = (
        f"Analyse this document for the following research goal: {goal}\n\n"
        f"DOCUMENT:\n{text[:4000]}\n\n"
        f"Respond in JSON:\n"
        f'{{"summary": "...", "findings": ["...", "..."], '
        f'"limitations": ["..."], "relevance": "HIGH|MEDIUM|LOW"}}'
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()

    # Extract JSON block if wrapped in markdown
    if "```" in raw:
        raw = raw.split("```")[1].lstrip("json").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"summary": raw, "findings": [], "limitations": [], "relevance": "MEDIUM"}

    source = f"Document {index + 1}"
    return DocumentAnalysis(
        index=index,
        source=source,
        summary=data.get("summary", ""),
        findings=data.get("findings", []),
        limitations=data.get("limitations", []),
        relevance=data.get("relevance", "MEDIUM"),
    )


def _synthesise(analyses: list[DocumentAnalysis], goal: str) -> tuple[str, list, list, list]:
    """Pass 2: cross-document synthesis."""
    context = "\n\n".join(
        f"[{a.source}]\nSummary: {a.summary}\n"
        f"Findings: {'; '.join(a.findings)}\n"
        f"Limitations: {'; '.join(a.limitations)}"
        for a in analyses
    )
    prompt = (
        f"Synthesise the following document analyses for the research goal: {goal}\n\n"
        f"ANALYSES:\n{context}\n\n"
        f"Respond in JSON:\n"
        f'{{"synthesis": "...", "themes": ["..."], '
        f'"agreements": ["..."], "conflicts": ["..."]}}'
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1].lstrip("json").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"synthesis": raw, "themes": [], "agreements": [], "conflicts": []}

    return (
        data.get("synthesis", ""),
        data.get("themes",     []),
        data.get("agreements", []),
        data.get("conflicts",  []),
    )


def _extract_structured(synthesis: str, analyses: list[DocumentAnalysis], goal: str) -> dict:
    """Pass 3: extract structured JSON from the synthesis for downstream use."""
    prompt = (
        f"Based on this synthesis, extract structured data relevant to: {goal}\n\n"
        f"SYNTHESIS:\n{synthesis[:3000]}\n\n"
        f"Return a JSON object with the most useful structured fields for this goal. "
        f"Include: key_facts (list), recommended_actions (list), confidence_level (string), "
        f"knowledge_gaps (list). Add domain-specific fields as appropriate."
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1].lstrip("json").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_extraction": raw}


def document_intelligence_pipeline(
    documents: list[str],
    analysis_goal: str,
    max_documents: int = 10,
    top_k_for_synthesis: int = 5,
    max_workers: int = 4,
) -> IntelligenceReport:
    """
    Run three-pass document intelligence.

    Args:
        documents:           Raw document texts to analyse.
        analysis_goal:       Research question or goal guiding the analysis.
        max_documents:       Cap on total documents to process (cost control).
        top_k_for_synthesis: Only the top-relevance documents proceed to Pass 2 + 3.
        max_workers:         Parallelism for Pass 1.
    """
    docs = documents[:max_documents]
    total = len(docs)

    # Pass 1 — parallel per-document analysis
    analyses: list[Optional[DocumentAnalysis]] = [None] * total
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_analyse_document, i, doc, analysis_goal): i
            for i, doc in enumerate(docs)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                analyses[idx] = future.result()
            except Exception as exc:
                print(f"  [warn] document {idx} analysis failed: {exc}")

    completed = [a for a in analyses if a is not None]

    # Rank by relevance: HIGH → MEDIUM → LOW, then take top_k
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    ranked = sorted(completed, key=lambda a: order.get(a.relevance, 3))
    top_docs = ranked[:top_k_for_synthesis]

    # Pass 2 — cross-document synthesis
    synthesis_text, themes, agreements, conflicts = _synthesise(top_docs, analysis_goal)

    # Pass 3 — structured extraction
    extracted = _extract_structured(synthesis_text, top_docs, analysis_goal)

    return IntelligenceReport(
        synthesis=synthesis_text,
        key_themes=themes,
        agreements=agreements,
        conflicts=conflicts,
        extracted=extracted,
        documents_used=len(top_docs),
        total_documents=total,
    )


# ── Quick smoke test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_docs = [
        "Multi-agent systems distribute work across specialised agents. "
        "An orchestrator decomposes the goal and assigns subtasks. "
        "Parallel execution reduces wall-clock time but introduces coordination overhead. "
        "Reliability depends on how failures at individual agents are handled.",

        "Agent reliability requires validation gates at each handoff boundary. "
        "Confidence thresholds prevent low-quality outputs from propagating. "
        "Circuit breakers protect downstream agents from cascading failures. "
        "Human escalation should trigger on confidence < threshold or on anomalous tool calls.",

        "Cost scales with context length and the number of model calls per task. "
        "Token budget management and model routing reduce costs 60-80% without quality loss. "
        "Per-task cost caps prevent runaway loops from exhausting budgets overnight.",
    ]

    goal = "What are the key reliability and cost considerations for multi-agent systems?"
    print(f"Goal: {goal}\n")

    report = document_intelligence_pipeline(sample_docs, goal)

    print(f"Documents analysed: {report.total_documents} total, {report.documents_used} used\n")
    print(f"Synthesis:\n{report.synthesis[:600]}\n")
    print(f"Key themes: {report.key_themes}")
    print(f"Agreements: {report.agreements}")
    print(f"Conflicts:  {report.conflicts}")
    print(f"\nStructured extraction:\n{json.dumps(report.extracted, indent=2)}")
