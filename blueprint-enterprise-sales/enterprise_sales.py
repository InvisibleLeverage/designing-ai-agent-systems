"""
Enterprise Sales Automation — Blueprint 5

Qualify → research → personalised outreach → nurture cadence.
Cost: $0.12–0.20 per qualified lead (Sonnet qualification, Opus high-tier outreach).

Key constraint: 3-sentence outreach rule with 1 specific verifiable fact and 0 adjectives
forces specificity — unconstrained agents write generic copy that gets deleted.
"""
import os
from dataclasses import dataclass, field
from typing import Optional

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))

OPUS   = "claude-opus-4-8"
SONNET = "claude-sonnet-4-6"
HAIKU  = "claude-haiku-4-5-20251001"

ICP_DEFINITION = """
Ideal Customer Profile:
- Company: 100–2000 employees, B2B SaaS or professional services
- Role: VP/Director/Head of Sales, RevOps, Marketing, or Product
- Stage: Series B+ or $10M+ ARR
- Signals: hiring for automation/AI roles, recent funding, revenue ops investment
- Deal size: $20K–$200K ARR
"""


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class Lead:
    name:    str
    company: str
    title:   str
    source:  str = "inbound"
    notes:   str = ""


@dataclass
class QualificationResult:
    score:             int          # 1–10
    tier:              str          # "high" | "nurture" | "discard"
    icp_fit_reasons:   list[str]
    disqualifiers:     list[str]
    recommended_action: str


@dataclass
class LeadDossier:
    lead:              Lead
    company_overview:  str
    pain_points:       list[str]
    trigger_events:    list[str]    # recent events making outreach timely
    decision_map:      str          # buying process + likely stakeholders
    data_gaps:         list[str]    # explicitly flagged missing info


@dataclass
class OutreachMessage:
    subject:           str
    body:              str
    channel:           str          # "email" | "linkedin"
    timing:            str          # "send_now" | "tuesday_9am" | etc.
    requires_review:   bool         # True for enterprise accounts


@dataclass
class NurtureSequence:
    day_5_message:     str
    day_12_message:    str   # breakup / last-attempt tone


# ── Agents ────────────────────────────────────────────────────────────────────

def qualify_lead(lead: Lead) -> QualificationResult:
    """Qualification Agent — score lead 1–10 vs ICP. Ambiguous signals → nurture, never discard."""
    enrichment = _stub_enrichment(lead.company)
    prompt = (
        f"Score this lead against our ICP criteria.\n\n"
        f"LEAD: {lead.name}, {lead.title} at {lead.company} (source: {lead.source})\n"
        f"ENRICHMENT:\n{enrichment}\n\n"
        f"ICP CRITERIA:\n{ICP_DEFINITION}\n\n"
        f"Respond:\n"
        f"SCORE: [1-10]\n"
        f"TIER: [high|nurture|discard]\n"
        f"ICP_FIT_REASONS:\n- [reason]\nDISQUALIFIERS:\n- [reason or 'None']\n"
        f"RECOMMENDED_ACTION: [full_research|light_sequence|log_and_stop]\n\n"
        f"Rule: if signals are ambiguous, tier = nurture (never discard on ambiguity)."
    )
    response = client.messages.create(
        model=SONNET, max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_qualification(response.content[0].text)


def research_lead(lead: Lead, qualification: QualificationResult) -> LeadDossier:
    """Research Agent — build dossier. Missing data → explicit gap; never invented."""
    enrichment = _stub_enrichment(lead.company)
    prompt = (
        f"Build a sales research dossier for {lead.name} ({lead.title} at {lead.company}).\n\n"
        f"ICP FIT REASONS: {'; '.join(qualification.icp_fit_reasons)}\n"
        f"ENRICHMENT DATA:\n{enrichment}\n\n"
        f"Provide:\n"
        f"COMPANY_OVERVIEW: [2 sentences, factual]\n"
        f"PAIN_POINTS:\n- [role-specific, not generic]\nTRIGGER_EVENTS:\n- [timely, verifiable]\n"
        f"DECISION_MAP: [buying process + likely stakeholders + budget holder]\n"
        f"DATA_GAPS:\n- [explicitly flag anything uncertain or missing]\n\n"
        f"Never invent facts. Flag gaps explicitly rather than filling with assumptions."
    )
    response = client.messages.create(
        model=OPUS, max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_dossier(response.content[0].text, lead)


def generate_outreach(
    dossier: LeadDossier, our_product: str, is_enterprise: bool = False
) -> OutreachMessage:
    """
    Outreach Agent — 3-sentence email. 1 specific fact, 0 adjectives, CTA with time.
    These constraints force specificity. Unconstrained agents write copy that gets deleted.
    """
    hooks   = "\n".join(f"- {t}" for t in dossier.trigger_events)
    pains   = "\n".join(f"- {p}" for p in dossier.pain_points[:2])
    prompt = (
        f"Write a personalised cold outreach email.\n\n"
        f"LEAD: {dossier.lead.name}, {dossier.lead.title} at {dossier.lead.company}\n"
        f"COMPANY OVERVIEW: {dossier.company_overview}\n"
        f"TRIGGER EVENTS (use exactly one):\n{hooks}\n"
        f"PAIN POINTS:\n{pains}\n"
        f"OUR PRODUCT: {our_product}\n\n"
        f"RULES (enforce strictly):\n"
        f"1. Body: exactly 3 sentences\n"
        f"2. Reference exactly 1 specific verifiable fact from trigger events\n"
        f"3. Zero adjectives (no 'innovative', 'powerful', 'leading', 'best-in-class')\n"
        f"4. Final sentence: specific CTA with a day/time (e.g. 'Open for 15 min Thursday?')\n"
        f"5. Subject: ≤ 8 words, no question marks\n\n"
        f"FORMAT:\nSUBJECT: ...\nBODY:\n..."
    )
    response = client.messages.create(
        model=SONNET, max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_outreach(response.content[0].text, is_enterprise)


def generate_nurture_sequence(dossier: LeadDossier) -> NurtureSequence:
    """Nurture Agent — Day 5 follow-up + Day 12 breakup. Haiku — low cost, high volume."""
    prompt = (
        f"Write two follow-up emails for {dossier.lead.name} at {dossier.lead.company}.\n\n"
        f"Context: {dossier.company_overview}\n"
        f"Pain points: {'; '.join(dossier.pain_points[:2])}\n\n"
        f"EMAIL_DAY_5 (different angle from initial email, ≤ 60 words):\nSUBJECT: ...\nBODY: ...\n\n"
        f"EMAIL_DAY_12 (genuine breakup — makes it easy to say no, ≤ 50 words):\nSUBJECT: ...\nBODY: ..."
    )
    response = client.messages.create(
        model=HAIKU, max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_nurture(response.content[0].text)


# ── Full pipeline ─────────────────────────────────────────────────────────────

def run_sales_pipeline(
    lead: Lead, our_product: str = "AI agent systems platform", is_enterprise: bool = False
) -> dict:
    """
    Full pipeline: qualify → research (high tier only) → outreach → nurture sequence.
    Returns a dict with all outputs and routing decisions.
    """
    qualification = qualify_lead(lead)
    result: dict = {"lead": lead, "qualification": qualification}

    if qualification.tier == "discard":
        result["action"] = "discarded"
        result["reason"] = qualification.disqualifiers
        return result

    if qualification.tier == "nurture":
        result["action"]  = "nurture_queue"
        dossier           = research_lead(lead, qualification)
        result["dossier"] = dossier
        result["nurture"] = generate_nurture_sequence(dossier)
        return result

    # High tier — full pipeline
    dossier            = research_lead(lead, qualification)
    outreach           = generate_outreach(dossier, our_product, is_enterprise)
    nurture            = generate_nurture_sequence(dossier)
    result.update({
        "action":             "full_outreach",
        "dossier":            dossier,
        "outreach":           outreach,
        "nurture":            nurture,
        "requires_review":    outreach.requires_review,
    })
    return result


# ── Parsers ───────────────────────────────────────────────────────────────────

def _parse_qualification(text: str) -> QualificationResult:
    data = {"score": 5, "tier": "nurture", "fit": [], "disq": [], "action": "light_sequence"}
    current = None
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("SCORE:"):
            try: data["score"] = int(s.split(":")[1].strip())
            except ValueError: pass
        elif s.startswith("TIER:"):
            raw = s.split(":")[1].strip().lower()
            data["tier"] = raw if raw in ("high","nurture","discard") else "nurture"
        elif s.startswith("ICP_FIT_REASONS:"): current = "fit"
        elif s.startswith("DISQUALIFIERS:"): current = "disq"
        elif s.startswith("RECOMMENDED_ACTION:"):
            data["action"] = s.split(":")[1].strip(); current = None
        elif s.startswith("- ") and current:
            item = s[2:].strip()
            if item and item.lower() != "none": data[current].append(item)
    score = data["score"]
    tier  = "high" if score >= 7 else ("nurture" if score >= 4 else "discard")
    return QualificationResult(
        score=score, tier=tier, icp_fit_reasons=data["fit"],
        disqualifiers=data["disq"], recommended_action=data["action"],
    )


def _parse_dossier(text: str, lead: Lead) -> LeadDossier:
    data = {"overview": "", "pains": [], "triggers": [], "map": "", "gaps": []}
    current = None
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("COMPANY_OVERVIEW:"): data["overview"] = s.split(":",1)[1].strip(); current = None
        elif s.startswith("PAIN_POINTS:"): current = "pains"
        elif s.startswith("TRIGGER_EVENTS:"): current = "triggers"
        elif s.startswith("DECISION_MAP:"): data["map"] = s.split(":",1)[1].strip(); current = None
        elif s.startswith("DATA_GAPS:"): current = "gaps"
        elif s.startswith("- ") and current: data[current].append(s[2:].strip())
    return LeadDossier(lead=lead, company_overview=data["overview"], pain_points=data["pains"],
                       trigger_events=data["triggers"], decision_map=data["map"], data_gaps=data["gaps"])


def _parse_outreach(text: str, is_enterprise: bool) -> OutreachMessage:
    subject, body_lines, in_body = "", [], False
    for line in text.split("\n"):
        if line.startswith("SUBJECT:"): subject = line.split(":",1)[1].strip()
        elif line.startswith("BODY:"): in_body = True
        elif in_body: body_lines.append(line)
    return OutreachMessage(subject=subject, body="\n".join(body_lines).strip(),
                           channel="email", timing="tuesday_9am", requires_review=is_enterprise)


def _parse_nurture(text: str) -> NurtureSequence:
    day5, day12, current, buf = "", "", None, []
    for line in text.split("\n"):
        if line.startswith("EMAIL_DAY_5"): current = "5"; buf = []
        elif line.startswith("EMAIL_DAY_12"):
            if current == "5": day5 = "\n".join(buf).strip()
            current = "12"; buf = []
        else:
            if current: buf.append(line)
    if current == "12": day12 = "\n".join(buf).strip()
    elif current == "5": day5 = "\n".join(buf).strip()
    return NurtureSequence(day_5_message=day5, day_12_message=day12)


def _stub_enrichment(company: str) -> str:
    return (
        f"Company: {company} | Employees: ~200 | Stage: Series B | Industry: B2B SaaS\n"
        f"Tech: Salesforce, HubSpot, Segment | Recent: hiring 5 RevOps roles this month\n"
        f"Note: replace with Apollo/Clearbit/Clay API for production."
    )


if __name__ == "__main__":
    lead = Lead(name="Marcus Webb", company="Apex Revenue", title="Head of Revenue Operations", source="LinkedIn")
    result = run_sales_pipeline(lead, our_product="AI agent automation platform")

    print(f"Lead:   {lead.name} @ {lead.company}")
    print(f"Score:  {result['qualification'].score} → {result['qualification'].tier.upper()}")
    print(f"Action: {result['action']}\n")

    if "outreach" in result:
        msg = result["outreach"]
        print(f"=== OUTREACH EMAIL ===")
        print(f"Subject: {msg.subject}")
        print(msg.body)
        print(f"\nReview required: {msg.requires_review}")

    if "nurture" in result:
        n = result["nurture"]
        print(f"\n=== DAY 5 FOLLOW-UP ===\n{n.day_5_message[:200]}")
        print(f"\n=== DAY 12 BREAKUP ===\n{n.day_12_message[:200]}")
