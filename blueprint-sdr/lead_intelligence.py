"""
Lead Intelligence Agent — Blueprint 1: AI SDR

Enriches a lead, scores ICP fit (0–100), and builds a research dossier.
High-tier leads (≥65) proceed to outreach. Mid-tier (40–64) → nurture. Low (<40) → discard.

Model: Opus — pain point mapping requires nuanced reasoning.
Cost: ~$0.04 per lead (Opus, 2K input + 800 output tokens).
"""
import os
from dataclasses import dataclass

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-opus-4-8"

ICP_CRITERIA = """
Ideal Customer Profile:
- Company size: 50–2000 employees
- Industry: SaaS, fintech, professional services, or e-commerce
- Role: VP/Director/Head of (Sales, Marketing, RevOps, Product)
- Signal: recent funding, hiring for AI/automation, or product-led growth motion
- Budget indicator: $50K–$500K ARR deals
"""


@dataclass
class LeadDossier:
    name:                str
    company:             str
    title:               str
    icp_score:           int          # 0–100
    icp_tier:            str          # "high" | "nurture" | "discard"
    icp_match_reasons:   list[str]
    company_overview:    str
    likely_pain_points:  list[str]
    conversation_hooks:  list[str]    # specific, verifiable facts to reference
    recommended_sequence: str         # "full_outreach" | "nurture" | "discard"


def build_lead_dossier(name: str, company: str, title: str, source: str = "") -> LeadDossier:
    """
    Build a full lead dossier with ICP scoring.
    Uses enrichment data stub — replace with Clearbit/Apollo/Clay API in production.
    """
    # Production: replace this stub with real enrichment API call
    enrichment_context = _stub_enrichment(company)

    prompt = f"""You are an expert B2B sales researcher. Analyse this lead and build a research dossier.

LEAD:
- Name: {name}
- Title: {title}
- Company: {company}
- Source: {source or "inbound"}

ENRICHMENT DATA:
{enrichment_context}

ICP CRITERIA:
{ICP_CRITERIA}

Respond in this exact format:

ICP_SCORE: [0-100 integer]
ICP_MATCH_REASONS:
- [reason 1]
- [reason 2]
COMPANY_OVERVIEW: [2-sentence factual overview]
LIKELY_PAIN_POINTS:
- [specific pain point relevant to their role and stage]
- [specific pain point]
- [specific pain point]
CONVERSATION_HOOKS:
- [specific verifiable fact about their company — not generic]
- [specific trigger event: funding/hiring/launch/award]
RECOMMENDED_SEQUENCE: [full_outreach | nurture | discard]

Be specific and role-aware. Pain points for a VP Sales differ from a Head of Product.
Never invent facts not supported by the enrichment data."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return _parse_dossier(response.content[0].text, name, company, title)


def _parse_dossier(text: str, name: str, company: str, title: str) -> LeadDossier:
    lines = text.strip().split("\n")
    data: dict = {
        "icp_score": 50, "icp_match_reasons": [], "company_overview": "",
        "likely_pain_points": [], "conversation_hooks": [], "recommended_sequence": "nurture",
    }
    current_list = None

    for line in lines:
        line = line.strip()
        if line.startswith("ICP_SCORE:"):
            try:
                data["icp_score"] = int(line.split(":")[1].strip())
            except ValueError:
                pass
        elif line.startswith("ICP_MATCH_REASONS:"):
            current_list = "icp_match_reasons"
        elif line.startswith("COMPANY_OVERVIEW:"):
            data["company_overview"] = line.split(":", 1)[1].strip()
            current_list = None
        elif line.startswith("LIKELY_PAIN_POINTS:"):
            current_list = "likely_pain_points"
        elif line.startswith("CONVERSATION_HOOKS:"):
            current_list = "conversation_hooks"
        elif line.startswith("RECOMMENDED_SEQUENCE:"):
            data["recommended_sequence"] = line.split(":")[1].strip().lower()
            current_list = None
        elif line.startswith("- ") and current_list:
            data[current_list].append(line[2:])

    score = data["icp_score"]
    tier  = "high" if score >= 65 else ("nurture" if score >= 40 else "discard")

    return LeadDossier(
        name=name, company=company, title=title,
        icp_score=score, icp_tier=tier,
        icp_match_reasons=data["icp_match_reasons"],
        company_overview=data["company_overview"],
        likely_pain_points=data["likely_pain_points"],
        conversation_hooks=data["conversation_hooks"],
        recommended_sequence=data["recommended_sequence"],
    )


def _stub_enrichment(company: str) -> str:
    """Stub — replace with Clearbit/Apollo/Clay API call in production."""
    return (
        f"Company: {company}\n"
        f"Employees: 150–300 (estimated)\n"
        f"Industry: B2B SaaS\n"
        f"Funding: Series B (estimated based on size)\n"
        f"Tech stack signals: Salesforce, HubSpot, Segment\n"
        f"Recent signals: hiring for RevOps and Sales Engineering roles\n"
        f"Note: enrich with real API (Clearbit/Apollo/Clay) for production use."
    )


if __name__ == "__main__":
    dossier = build_lead_dossier(
        name="Sarah Chen",
        company="Meridian Analytics",
        title="VP of Sales",
        source="LinkedIn inbound",
    )

    print(f"ICP Score:  {dossier.icp_score} ({dossier.icp_tier.upper()})")
    print(f"Tier:       {dossier.icp_tier}")
    print(f"Overview:   {dossier.company_overview}")
    print(f"\nPain Points:")
    for p in dossier.likely_pain_points:
        print(f"  • {p}")
    print(f"\nConversation Hooks:")
    for h in dossier.conversation_hooks:
        print(f"  • {h}")
    print(f"\nRecommended: {dossier.recommended_sequence}")
