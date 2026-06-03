"""
Engagement Monitor — Blueprint 1: AI SDR

Routes engagement signals after outreach is sent.
  Hot (reply / click / meeting booked) → immediate human handoff package
  Cold (no engagement after 14 days)   → sequence ends; re-score lead in 60 days
  Autoresponder                         → excluded from handoff (header check)

Hard rule: never send an automated reply to a reply. Any reply = human takes over.
"""
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))
MODEL  = "claude-sonnet-4-6"


class SignalType(str, Enum):
    REPLY           = "reply"
    CLICK           = "click"
    OPEN            = "open"
    MEETING_BOOKED  = "meeting_booked"
    BOUNCE          = "bounce"
    SPAM            = "spam"
    NO_ENGAGEMENT   = "no_engagement"


class RouteDecision(str, Enum):
    HUMAN_HANDOFF   = "human_handoff"    # rep takes over immediately
    CONTINUE        = "continue"         # next email in sequence
    END_SEQUENCE    = "end_sequence"     # 14-day window expired
    DISCARD         = "discard"          # bounce or spam


@dataclass
class EngagementEvent:
    lead_id:      str
    signal:       SignalType
    timestamp:    float = field(default_factory=time.time)
    email_index:  int   = 1      # which email triggered this (1, 2, or 3)
    reply_text:   Optional[str] = None
    is_autoresponder: bool = False


@dataclass
class HandoffPackage:
    lead_id:        str
    lead_name:      str
    company:        str
    signal:         SignalType
    reply_text:     Optional[str]
    conversation_summary: str
    suggested_next_step:  str
    urgency:        str          # "immediate" | "within_24h" | "this_week"


def route_engagement(event: EngagementEvent, lead_context: dict) -> RouteDecision:
    """
    Route an engagement event to the appropriate action.
    Returns a RouteDecision; callers generate HandoffPackage when HUMAN_HANDOFF.
    """
    if event.is_autoresponder:
        return RouteDecision.CONTINUE

    if event.signal in (SignalType.REPLY, SignalType.MEETING_BOOKED):
        return RouteDecision.HUMAN_HANDOFF

    if event.signal == SignalType.BOUNCE:
        return RouteDecision.DISCARD

    if event.signal == SignalType.SPAM:
        return RouteDecision.DISCARD

    if event.signal == SignalType.CLICK:
        # High-intent signal — prep handoff but continue sequence if no reply
        days_in_sequence = (time.time() - lead_context.get("sequence_start", time.time())) / 86400
        return RouteDecision.HUMAN_HANDOFF if days_in_sequence > 5 else RouteDecision.CONTINUE

    if event.signal == SignalType.NO_ENGAGEMENT:
        days_in_sequence = (time.time() - lead_context.get("sequence_start", time.time())) / 86400
        return RouteDecision.END_SEQUENCE if days_in_sequence >= 14 else RouteDecision.CONTINUE

    return RouteDecision.CONTINUE


def build_handoff_package(
    event: EngagementEvent,
    lead_context: dict,
) -> HandoffPackage:
    """
    Build a rep handoff package using AI to summarise context and suggest next step.
    Called only when route_engagement returns HUMAN_HANDOFF.
    """
    reply_section = f"\nLEAD'S REPLY:\n{event.reply_text}" if event.reply_text else ""
    dossier_summary = "\n".join(
        f"- {k}: {v}" for k, v in lead_context.items()
        if k in ("pain_points", "conversation_hooks", "icp_score", "company_overview")
    )

    prompt = f"""A sales lead has engaged. Build a rep handoff package.

LEAD: {lead_context.get('name', 'Unknown')} — {lead_context.get('title', '')} @ {lead_context.get('company', '')}
SIGNAL: {event.signal.value} (Email {event.email_index} of 3)
{reply_section}

RESEARCH DOSSIER:
{dossier_summary}

Write:
CONVERSATION_SUMMARY: [2-sentence summary of what we know and what triggered engagement]
SUGGESTED_NEXT_STEP: [specific action for the rep — be concrete, not generic]
URGENCY: [immediate | within_24h | this_week — and why]"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )

    text  = response.content[0].text
    parts = _parse_handoff(text)

    return HandoffPackage(
        lead_id=event.lead_id,
        lead_name=lead_context.get("name", ""),
        company=lead_context.get("company", ""),
        signal=event.signal,
        reply_text=event.reply_text,
        conversation_summary=parts.get("summary", ""),
        suggested_next_step=parts.get("next_step", ""),
        urgency=parts.get("urgency", "within_24h"),
    )


def is_autoresponder(reply_text: str, headers: dict) -> bool:
    """Detect autoresponders via header check and content heuristics."""
    auto_headers = {"auto-submitted", "x-auto-response-suppress", "x-autorespond"}
    if any(h.lower() in headers for h in auto_headers):
        return True
    patterns = [
        r"out of (the )?office", r"automatic reply", r"auto[- ]?reply",
        r"i am (currently )?away", r"on vacation", r"on leave",
    ]
    return any(re.search(p, reply_text.lower()) for p in patterns)


def _parse_handoff(text: str) -> dict:
    result = {}
    for line in text.split("\n"):
        if line.startswith("CONVERSATION_SUMMARY:"):
            result["summary"] = line.split(":", 1)[1].strip()
        elif line.startswith("SUGGESTED_NEXT_STEP:"):
            result["next_step"] = line.split(":", 1)[1].strip()
        elif line.startswith("URGENCY:"):
            raw = line.split(":", 1)[1].strip().lower()
            result["urgency"] = next(
                (u for u in ("immediate", "within_24h", "this_week") if u in raw),
                "within_24h",
            )
    return result


if __name__ == "__main__":
    lead_ctx = {
        "name": "Sarah Chen", "title": "VP of Sales", "company": "Meridian Analytics",
        "icp_score": 78,
        "company_overview": "B2B SaaS providing revenue intelligence to mid-market sales teams.",
        "pain_points": "SDRs spending 60%+ time on research; inconsistent lead scoring",
        "conversation_hooks": "Posting 3 RevOps roles; G2 review mentions data entry burden",
        "sequence_start": time.time() - 3 * 86400,
    }

    event = EngagementEvent(
        lead_id="lead_001",
        signal=SignalType.REPLY,
        email_index=1,
        reply_text="Hi — this is interesting timing. We're actually evaluating tools in this space. Can we set up a 20-minute call next week?",
    )

    decision = route_engagement(event, lead_ctx)
    print(f"Route decision: {decision.value}")

    if decision == RouteDecision.HUMAN_HANDOFF:
        pkg = build_handoff_package(event, lead_ctx)
        print(f"\n=== HANDOFF PACKAGE ===")
        print(f"Lead:      {pkg.lead_name} @ {pkg.company}")
        print(f"Signal:    {pkg.signal.value}")
        print(f"Urgency:   {pkg.urgency}")
        print(f"Summary:   {pkg.conversation_summary}")
        print(f"Next step: {pkg.suggested_next_step}")
        if pkg.reply_text:
            print(f"Reply:     {pkg.reply_text[:150]}")
