"""
Production Research Pipeline — Blueprint 6

Enterprise research pipeline with source caching, semantic memory, per-claim confidence,
and cost controls. Extends Blueprint 2 with the production infrastructure.

Production swap-ins:
  - SourceCache  → Redis (set TTL=86400 per key)
  - ResearchMemory → Pinecone / Weaviate (cosine similarity over stored report embeddings)
  - web_search() → Exa / Serper / Brave API
"""
import asyncio
import hashlib
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

OPUS   = "claude-opus-4-8"
SONNET = "claude-sonnet-4-6"
HAIKU  = "claude-haiku-4-5-20251001"

MEMORY_SIMILARITY_THRESHOLD = 0.70   # reuse prior research above this overlap
SOURCE_CACHE_TTL            = 86_400  # 24 hours in seconds
MAX_COST_PER_TASK_USD       = 2.00


# ── Source Cache (stub → replace with Redis) ──────────────────────────────────

class SourceCache:
    """In-memory stub. Replace with Redis in production (TTL=86400)."""
    def __init__(self, ttl: int = SOURCE_CACHE_TTL):
        self._store: dict[str, tuple[str, float]] = {}
        self._ttl   = ttl

    def get(self, url: str) -> Optional[str]:
        if url in self._store:
            content, stored_at = self._store[url]
            if time.time() - stored_at < self._ttl:
                return content
            del self._store[url]
        return None

    def set(self, url: str, content: str) -> None:
        self._store[url] = (content, time.time())

    def cache_key(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]


# ── Research Memory (stub → replace with Pinecone/Weaviate) ──────────────────

@dataclass
class StoredReport:
    brief:      str
    synthesis:  str
    stored_at:  float = field(default_factory=time.time)


class ResearchMemory:
    """In-memory stub. Replace with vector store for semantic similarity in production."""
    def __init__(self):
        self._reports: list[StoredReport] = []

    def store(self, brief: str, synthesis: str) -> None:
        self._reports.append(StoredReport(brief=brief, synthesis=synthesis))

    def find_similar(self, brief: str, threshold: float = MEMORY_SIMILARITY_THRESHOLD) -> Optional[StoredReport]:
        """
        Stub: keyword overlap similarity.
        Production: embed brief → cosine similarity over stored report embeddings.
        """
        brief_terms = set(brief.lower().split())
        for report in reversed(self._reports):   # most recent first
            report_terms = set(report.brief.lower().split())
            overlap = len(brief_terms & report_terms) / max(len(brief_terms), 1)
            if overlap >= threshold:
                return report
        return None


# ── Cost tracker ──────────────────────────────────────────────────────────────

class TaskCostTracker:
    _RATES = {
        OPUS:   (15.00, 75.00),
        SONNET: (3.00,  15.00),
        HAIKU:  (0.80,  4.00),
    }

    def __init__(self, budget: float = MAX_COST_PER_TASK_USD):
        self._budget = budget
        self._spent  = 0.0

    def record(self, model: str, input_tokens: int, output_tokens: int) -> float:
        inp, out = self._RATES.get(model, (3.00, 15.00))
        cost = (input_tokens * inp + output_tokens * out) / 1_000_000
        self._spent += cost
        return cost

    @property
    def within_budget(self) -> bool:
        return self._spent < self._budget

    @property
    def total_spent(self) -> float:
        return round(self._spent, 4)


# ── Research agents ───────────────────────────────────────────────────────────

def _call(model: str, system: str, user: str, max_tokens: int, tracker: TaskCostTracker) -> str:
    if not tracker.within_budget:
        return f"[BUDGET_EXCEEDED — task cost cap ${MAX_COST_PER_TASK_USD} reached]"
    r = client.messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}],
    )
    tracker.record(model, r.usage.input_tokens, r.usage.output_tokens)
    return r.content[0].text.strip()


def web_search_agent(subtask: str, tracker: TaskCostTracker, cache: SourceCache) -> str:
    cache_key = cache.cache_key(subtask)
    cached    = cache.get(cache_key)
    if cached:
        return f"[CACHED] {cached}"

    # Production: replace with Exa/Serper/Brave API call
    search_results = f"[Stub web search for: {subtask}] Replace with real search API."
    result = _call(
        SONNET,
        system="You are a research agent. Summarise search results factually. Flag unverifiable claims.",
        user=f"Research task: {subtask}\n\nSearch results:\n{search_results}\n\nSummarise key findings. Flag any gaps.",
        max_tokens=600, tracker=tracker,
    )
    cache.set(cache_key, result)
    return result


def document_reader_agent(doc_path: str, question: str, tracker: TaskCostTracker, cache: SourceCache) -> str:
    cached = cache.get(doc_path)
    if cached:
        return _call(
            SONNET,
            system="Answer from the provided document text only.",
            user=f"Document:\n{cached[:3000]}\n\nQuestion: {question}",
            max_tokens=500, tracker=tracker,
        )
    # Production: replace with Unstructured.io / PyMuPDF
    return f"[Document reader stub for: {doc_path}] Replace with real document parser."


def synthesise(subtask_results: list[str], brief: str, tracker: TaskCostTracker) -> str:
    context = "\n\n".join(f"[Result {i+1}]\n{r}" for i, r in enumerate(subtask_results))
    return _call(
        OPUS,
        system="You are a senior research analyst. Synthesise clearly. Assign confidence (HIGH/MEDIUM/LOW) to each major claim.",
        user=(
            f"Original brief: {brief}\n\nResearch results:\n{context}\n\n"
            f"Write a unified research brief with per-claim confidence. "
            f"Format claims as: [HIGH] claim | [MEDIUM] claim | [LOW] claim. "
            f"Surface contradictions — don't hide them. Identify knowledge gaps."
        ),
        max_tokens=2000, tracker=tracker,
    )


def quality_check(synthesis: str, brief: str, tracker: TaskCostTracker) -> list[str]:
    text = _call(
        HAIKU,
        system="You are a quality reviewer for research reports.",
        user=(
            f"Original brief: {brief}\n\nSynthesis:\n{synthesis[:2000]}\n\n"
            f"List:\n1. Knowledge gaps (what the brief asked that was not answered)\n"
            f"2. Claims needing human verification (numbers, dates, regulatory claims)\n"
            f"One item per line. Start gaps with 'GAP:' and flags with 'VERIFY:'"
        ),
        max_tokens=400, tracker=tracker,
    )
    return [
        line.strip()
        for line in text.split("\n")
        if line.strip().startswith(("GAP:", "VERIFY:"))
    ]


def supplement_from_prior(prior: StoredReport, brief: str, tracker: TaskCostTracker) -> str:
    """Run only the delta — what the prior report doesn't cover."""
    return _call(
        SONNET,
        system="You are a research analyst supplementing an existing report.",
        user=(
            f"Prior research:\n{prior.synthesis[:1500]}\n\n"
            f"New brief: {brief}\n\n"
            f"Identify what the new brief asks that the prior research doesn't cover. "
            f"Provide only the supplementary information needed. "
            f"Mark clearly: [FROM PRIOR RESEARCH] vs [NEW RESEARCH]."
        ),
        max_tokens=800, tracker=tracker,
    )


# ── Main pipeline ─────────────────────────────────────────────────────────────

@dataclass
class ProductionResearchReport:
    brief:              str
    synthesis:          str
    quality_flags:      list[str]
    served_from_cache:  bool
    tasks_run:          int
    cost_usd:           float
    elapsed_seconds:    float


async def run_research_with_cache(
    brief: str,
    subtasks: Optional[list[str]] = None,
    cache:    Optional[SourceCache]    = None,
    memory:   Optional[ResearchMemory] = None,
) -> ProductionResearchReport:
    start   = time.time()
    cache   = cache  or SourceCache()
    memory  = memory or ResearchMemory()
    tracker = TaskCostTracker()

    # Memory check
    prior = memory.find_similar(brief)
    if prior:
        synthesis = supplement_from_prior(prior, brief, tracker)
        flags     = quality_check(synthesis, brief, tracker)
        memory.store(brief, synthesis)
        return ProductionResearchReport(
            brief=brief, synthesis=synthesis, quality_flags=flags,
            served_from_cache=True, tasks_run=1,
            cost_usd=tracker.total_spent, elapsed_seconds=round(time.time() - start, 1),
        )

    # Full run — parallel subtasks
    tasks = subtasks or [
        f"Company background and recent developments: {brief}",
        f"Industry context and competitive landscape: {brief}",
        f"Key risks and opportunities: {brief}",
    ]

    loop    = asyncio.get_event_loop()
    futures = [loop.run_in_executor(None, web_search_agent, t, tracker, cache) for t in tasks]
    results = list(await asyncio.gather(*futures))

    synthesis = synthesise(results, brief, tracker)
    flags     = quality_check(synthesis, brief, tracker)
    memory.store(brief, synthesis)

    return ProductionResearchReport(
        brief=brief, synthesis=synthesis, quality_flags=flags,
        served_from_cache=False, tasks_run=len(tasks),
        cost_usd=tracker.total_spent, elapsed_seconds=round(time.time() - start, 1),
    )


if __name__ == "__main__":
    shared_cache  = SourceCache()
    shared_memory = ResearchMemory()

    brief1 = "Research Stripe's competitive position in the payments market for an enterprise sales call."
    report1 = asyncio.run(run_research_with_cache(brief1, cache=shared_cache, memory=shared_memory))

    print(f"=== RUN 1 ===")
    print(f"Tasks run:    {report1.tasks_run}  |  From cache: {report1.served_from_cache}")
    print(f"Cost:         ${report1.cost_usd}  |  Time: {report1.elapsed_seconds}s")
    print(f"Flags:        {len(report1.quality_flags)}")
    print(f"\nSynthesis (first 500 chars):\n{report1.synthesis[:500]}...")

    # Second query with high overlap — should hit memory
    brief2 = "Research Stripe for an investor briefing on their enterprise payments market position."
    report2 = asyncio.run(run_research_with_cache(brief2, cache=shared_cache, memory=shared_memory))

    print(f"\n=== RUN 2 (similar brief) ===")
    print(f"Tasks run:    {report2.tasks_run}  |  From cache: {report2.served_from_cache}")
    print(f"Cost:         ${report2.cost_usd}  |  Time: {report2.elapsed_seconds}s")

    if report1.quality_flags:
        print(f"\nQuality flags:")
        for f in report1.quality_flags:
            print(f"  {f}")
