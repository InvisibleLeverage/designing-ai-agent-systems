"""
Autonomous Research Pipeline — Blueprint 2

Decompose → parallel specialist agents → synthesize → verification flags.
Replaces 4–8 hours of manual research with an 8–12 minute automated brief.

Production swap-ins:
  - Replace stub web_search() with Exa / Serper / Brave API
  - Replace stub fetch_document() with Unstructured.io / PyMuPDF
"""
import asyncio
import os
import time
from dataclasses import dataclass, field

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))

OPUS   = "claude-opus-4-8"
SONNET = "claude-sonnet-4-6"
HAIKU  = "claude-haiku-4-5-20251001"


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class ResearchTask:
    task_type:   str   # "company_profile" | "industry_analysis" | "competitive_intel"
    subject:     str
    question:    str
    source_type: str   # "web" | "document" | "database"


@dataclass
class TaskResult:
    task_type:  str
    subject:    str
    content:    str
    confidence: str   # "HIGH" | "MEDIUM" | "LOW"
    gaps:       list[str] = field(default_factory=list)


@dataclass
class ResearchReport:
    brief:               str
    tasks_completed:     int
    synthesis:           str
    verification_flags:  list[str]
    confidence_summary:  dict
    elapsed_seconds:     float


# ── Agent functions ───────────────────────────────────────────────────────────

def _call(model: str, system: str, user: str, max_tokens: int = 1024) -> str:
    response = client.messages.create(
        model=model, max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text.strip()


def decompose_brief(brief: str) -> list[ResearchTask]:
    """Decomposition Agent — parse natural language brief into typed parallel subtasks."""
    text = _call(
        OPUS,
        system="You are a research director. Parse research briefs into structured subtasks.",
        user=(
            f"Parse this research brief into subtasks:\n\n{brief}\n\n"
            f"For each subtask, write one line:\n"
            f"TASK: [company_profile|industry_analysis|competitive_intel] | [subject] | [specific question] | [web|document|database]\n"
            f"Generate 3–5 tasks. Cover company, industry context, and competitive landscape."
        ),
        max_tokens=512,
    )

    tasks = []
    for line in text.split("\n"):
        if line.startswith("TASK:"):
            parts = [p.strip() for p in line[5:].split("|")]
            if len(parts) == 4:
                tasks.append(ResearchTask(
                    task_type=parts[0], subject=parts[1],
                    question=parts[2], source_type=parts[3],
                ))
    return tasks or [
        ResearchTask("company_profile", "target company", brief, "web"),
        ResearchTask("industry_analysis", "industry", brief, "web"),
        ResearchTask("competitive_intel", "competitors", brief, "web"),
    ]


def run_company_profiler(task: ResearchTask) -> TaskResult:
    search_results = _stub_web_search(task.subject, task.question)
    content = _call(
        SONNET,
        system="You are a company research analyst. Be factual. Flag missing data explicitly — never invent.",
        user=(
            f"Research question: {task.question}\n\nSearch results:\n{search_results}\n\n"
            f"Provide: company overview (2–3 sentences), key facts (headcount, stage, product), "
            f"recent developments, and any data gaps.\n"
            f"End with: CONFIDENCE: [HIGH|MEDIUM|LOW]"
        ),
        max_tokens=800,
    )
    return _parse_task_result("company_profile", task.subject, content)


def run_industry_analyst(task: ResearchTask) -> TaskResult:
    search_results = _stub_web_search(task.subject, task.question)
    content = _call(
        SONNET,
        system="You are an industry analyst. Cite conflicting signals — don't reconcile them artificially.",
        user=(
            f"Research question: {task.question}\n\nSearch results:\n{search_results}\n\n"
            f"Provide: market context, key trends (2–3), competitive dynamics, and growth signals.\n"
            f"If signals conflict, surface both. End with: CONFIDENCE: [HIGH|MEDIUM|LOW]"
        ),
        max_tokens=800,
    )
    return _parse_task_result("industry_analysis", task.subject, content)


def run_competitive_intel(task: ResearchTask) -> TaskResult:
    search_results = _stub_web_search(task.subject, task.question)
    content = _call(
        SONNET,
        system="You are a competitive intelligence analyst. Never invent differentiators — flag gaps explicitly.",
        user=(
            f"Research question: {task.question}\n\nSearch results:\n{search_results}\n\n"
            f"Provide: key competitors, differentiation map, positioning gaps, and threats.\n"
            f"If data is insufficient, say so. End with: CONFIDENCE: [HIGH|MEDIUM|LOW]"
        ),
        max_tokens=800,
    )
    return _parse_task_result("competitive_intel", task.subject, content)


def synthesise_results(results: list[TaskResult], brief: str) -> str:
    context = "\n\n".join(
        f"[{r.task_type.upper()} — {r.subject}]\n{r.content}"
        for r in results
    )
    return _call(
        OPUS,
        system="You are a senior research analyst. Synthesise clearly. Surface contradictions rather than hiding them.",
        user=(
            f"Original brief: {brief}\n\nResearch results:\n{context}\n\n"
            f"Write a unified research brief: key findings, strategic context, risks, and knowledge gaps. "
            f"Note any contradictions between sources. 400–600 words."
        ),
        max_tokens=1500,
    )


def extract_verification_flags(synthesis: str) -> list[str]:
    """Haiku — fast scan for claims needing human verification."""
    text = _call(
        HAIKU,
        system="You are a fact-checker. Identify claims that require verification.",
        user=(
            f"Scan this research synthesis and list claims that need human verification:\n\n{synthesis}\n\n"
            f"Flag: specific numbers, recent events (last 90 days), regulatory/legal claims, "
            f"revenue/valuation figures, and any claim with a source not cited.\n"
            f"Format: one flag per line starting with 'FLAG:'"
        ),
        max_tokens=512,
    )
    return [
        line[5:].strip()
        for line in text.split("\n")
        if line.strip().startswith("FLAG:")
    ]


# ── Pipeline orchestration ────────────────────────────────────────────────────

async def _run_task_async(task: ResearchTask) -> TaskResult:
    loop = asyncio.get_event_loop()
    runners = {
        "company_profile":   run_company_profiler,
        "industry_analysis": run_industry_analyst,
        "competitive_intel": run_competitive_intel,
    }
    runner = runners.get(task.task_type, run_company_profiler)
    return await loop.run_in_executor(None, runner, task)


async def run_research_pipeline(brief: str) -> ResearchReport:
    start = time.time()

    tasks   = decompose_brief(brief)
    results = await asyncio.gather(*[_run_task_async(t) for t in tasks])
    results = [r for r in results if r is not None]

    synthesis = synthesise_results(results, brief)
    flags     = extract_verification_flags(synthesis)

    confidence_summary = {
        level: sum(1 for r in results if r.confidence == level)
        for level in ("HIGH", "MEDIUM", "LOW")
    }

    return ResearchReport(
        brief=brief,
        tasks_completed=len(results),
        synthesis=synthesis,
        verification_flags=flags,
        confidence_summary=confidence_summary,
        elapsed_seconds=round(time.time() - start, 1),
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_task_result(task_type: str, subject: str, content: str) -> TaskResult:
    confidence = "MEDIUM"
    for level in ("HIGH", "MEDIUM", "LOW"):
        if f"CONFIDENCE: {level}" in content:
            confidence = level
            break
    return TaskResult(task_type=task_type, subject=subject,
                      content=content, confidence=confidence)


def _stub_web_search(subject: str, question: str) -> str:
    """Stub — replace with Exa / Serper / Brave API in production."""
    return (
        f"[Stub search results for '{subject}': {question}]\n"
        f"Note: Replace with real search API (Exa/Serper/Brave) for production.\n"
        f"Real results would include: company website, news articles, LinkedIn, Crunchbase."
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    brief = (
        "Research Acme Corp for an enterprise sales meeting next week. "
        "I need to understand their business model, recent growth signals, "
        "competitive position, and likely pain points for a VP of Engineering."
    )

    report = asyncio.run(run_research_pipeline(brief))

    print(f"Tasks completed:  {report.tasks_completed}")
    print(f"Elapsed:          {report.elapsed_seconds}s")
    print(f"Confidence:       {report.confidence_summary}")
    print(f"\n=== SYNTHESIS ===\n{report.synthesis[:800]}...")
    print(f"\n=== VERIFICATION FLAGS ({len(report.verification_flags)}) ===")
    for flag in report.verification_flags:
        print(f"  ⚠ {flag}")
