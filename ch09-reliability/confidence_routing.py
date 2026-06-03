"""
Confidence Routing — Chapter 9: System Reliability and Safety

Agents self-report confidence on every output. Outputs below threshold are
queued for human review instead of being published directly.

The system prompt suffix that enables self-reporting is included here —
append it to any agent system prompt to get structured confidence signals.
"""
import re
from dataclasses import dataclass, field
from queue import Queue
from typing import Optional


CONFIDENCE_PROMPT_SUFFIX = """
After your response, append exactly one line in this format:
CONFIDENCE: [HIGH|MEDIUM|LOW] [0-100]
Reason: [one sentence explaining your confidence level]

HIGH   = certain of facts and reasoning; sources are clear and unambiguous
MEDIUM = reasonable confidence but some gaps or assumptions exist
LOW    = uncertain; reasoning is outside my knowledge or data is missing
"""

PUBLISH_THRESHOLD   = 0.60   # scores below this go to human review queue
CONFIDENCE_PATTERN  = re.compile(r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)\s+(\d+)', re.IGNORECASE)

LEVEL_TO_SCORE = {"HIGH": 0.90, "MEDIUM": 0.65, "LOW": 0.30}


@dataclass
class ConfidenceResult:
    level:          str           # "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN"
    score:          float         # 0.0 – 1.0
    reason:         str
    clean_output:   str           # output with the CONFIDENCE line stripped
    status:         str           # "published" | "queued_for_review"
    raw_confidence: str           # the raw CONFIDENCE line for debugging


@dataclass
class ReviewQueueItem:
    task_id:    str
    output:     str
    confidence: ConfidenceResult
    context:    dict = field(default_factory=dict)


class HumanReviewQueue:
    """Simple in-memory review queue. Replace with a ticketing system or Slack webhook."""

    def __init__(self):
        self._queue: Queue = Queue()

    def push(self, item: ReviewQueueItem) -> None:
        self._queue.put(item)

    def pop(self) -> Optional[ReviewQueueItem]:
        return self._queue.get_nowait() if not self._queue.empty() else None

    def depth(self) -> int:
        return self._queue.qsize()


def parse_confidence(response: str) -> tuple[str, float, str, str]:
    """
    Extract CONFIDENCE level, score, reason, and raw line from response.
    Returns (level, score, reason, raw_line).
    Falls back to UNKNOWN at 0.5 if no CONFIDENCE line found.
    """
    match = CONFIDENCE_PATTERN.search(response)
    if not match:
        return "UNKNOWN", 0.5, "No confidence signal found", ""

    level      = match.group(1).upper()
    raw_score  = int(match.group(2))
    score      = raw_score / 100.0

    # Extract reason line if present
    reason = ""
    reason_match = re.search(r'Reason:\s*(.+)', response, re.IGNORECASE)
    if reason_match:
        reason = reason_match.group(1).strip()

    raw_line = match.group(0)
    return level, score, reason, raw_line


def strip_confidence_line(response: str) -> str:
    """Remove the CONFIDENCE and Reason lines from the output before publishing."""
    cleaned = re.sub(r'\nCONFIDENCE:.*', '', response, flags=re.IGNORECASE)
    cleaned = re.sub(r'\nReason:.*',     '', cleaned, flags=re.IGNORECASE)
    return cleaned.rstrip()


def route_by_confidence(
    response:      str,
    review_queue:  HumanReviewQueue,
    task_id:       str = "",
    threshold:     float = PUBLISH_THRESHOLD,
    context:       Optional[dict] = None,
) -> ConfidenceResult:
    """
    Parse confidence from response and route:
      score >= threshold → status="published"
      score <  threshold → push to review_queue, status="queued_for_review"

    Returns ConfidenceResult with clean_output (confidence lines stripped).
    """
    level, score, reason, raw_line = parse_confidence(response)
    clean_output = strip_confidence_line(response)

    if score >= threshold:
        status = "published"
    else:
        status = "queued_for_review"
        review_queue.push(ReviewQueueItem(
            task_id=task_id or "unknown",
            output=clean_output,
            confidence=ConfidenceResult(
                level=level, score=score, reason=reason,
                clean_output=clean_output, status=status, raw_confidence=raw_line,
            ),
            context=context or {},
        ))

    return ConfidenceResult(
        level=level,
        score=score,
        reason=reason,
        clean_output=clean_output,
        status=status,
        raw_confidence=raw_line,
    )


# ── Quick smoke test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    review_q = HumanReviewQueue()

    # Simulate agent outputs with different confidence levels
    responses = [
        (
            "The Transformer architecture was introduced in 'Attention Is All You Need' (Vaswani et al., 2017). "
            "It uses self-attention to process sequences in parallel.\n"
            "CONFIDENCE: HIGH 92\nReason: Well-documented fact from primary source."
        ),
        (
            "The company's Q3 revenue was approximately $142M, representing 18% growth.\n"
            "CONFIDENCE: MEDIUM 58\nReason: Based on available reports but exact figure not confirmed."
        ),
        (
            "I believe the regulation requires disclosure within 72 hours, but I am not certain.\n"
            "CONFIDENCE: LOW 25\nReason: Outside my reliable knowledge; regulatory details change frequently."
        ),
        (
            "Here is a summary of the findings."   # no confidence line
        ),
    ]

    for i, response in enumerate(responses):
        result = route_by_confidence(response, review_q, task_id=f"task_{i}")
        print(f"Task {i}: [{result.level:7s}] score={result.score:.2f} → {result.status}")
        if result.reason:
            print(f"         Reason: {result.reason}")

    print(f"\nReview queue depth: {review_q.depth()}")
    print(f"\nSystem prompt suffix to add to any agent:\n{CONFIDENCE_PROMPT_SUFFIX}")
