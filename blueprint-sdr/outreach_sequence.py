"""
Outreach Sequence Generator — Blueprint 1: AI SDR

Generates a personalised 3-email sequence from a LeadDossier.
Email 1: hook + one specific fact. Email 2 (Day 5): different angle. Email 3 (Day 12): breakup.

Rules enforced in prompt:
  - Email 1: < 100 words
  - Each email references exactly one verifiable fact from the dossier
  - No adjectives ("innovative", "cutting-edge", "game-changing")
  - Clear CTA with specific ask in every email
"""
import os
from dataclasses import dataclass

import anthropic

from lead_intelligence import LeadDossier

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL  = "claude-opus-4-8"


@dataclass
class OutreachSequence:
    lead_name:    str
    company:      str
    email_1:      str   # Day 0 — hook + specific fact
    email_2:      str   # Day 5 — different angle
    email_3:      str   # Day 12 — breakup / last attempt
    requires_review: bool   # True for enterprise accounts


def generate_outreach_sequence(
    dossier: LeadDossier,
    our_product: str = "AI agent systems platform",
    is_enterprise: bool = False,
) -> OutreachSequence:
    """
    Generate a 3-email personalised outreach sequence.
    Enterprise leads are flagged for human review before sending.
    """
    hooks  = "\n".join(f"- {h}" for h in dossier.conversation_hooks)
    pains  = "\n".join(f"- {p}" for p in dossier.likely_pain_points[:2])
    reasons = "\n".join(f"- {r}" for r in dossier.icp_match_reasons[:2])

    prompt = f"""Write a 3-email outreach sequence for this lead. Follow the rules exactly.

LEAD:
- Name: {dossier.name}
- Title: {dossier.title}, {dossier.company}
- ICP score: {dossier.icp_score}
- Company overview: {dossier.company_overview}

CONVERSATION HOOKS (verifiable facts — use exactly one per email):
{hooks}

LIKELY PAIN POINTS:
{pains}

ICP MATCH REASONS:
{reasons}

OUR PRODUCT: {our_product}

RULES (non-negotiable):
1. Email 1: under 100 words. Subject line + body only.
2. Each email: reference exactly ONE specific verifiable fact from conversation hooks.
3. Zero adjectives. No "innovative", "cutting-edge", "game-changing", "powerful", "robust".
4. Every email has a specific CTA (not "let me know if interested").
5. Email 3 is a genuine breakup email — makes it easy to say no.
6. Write for {dossier.title} — not a generic salesperson.

FORMAT:
EMAIL_1_SUBJECT: ...
EMAIL_1_BODY:
...

EMAIL_2_SUBJECT: ...
EMAIL_2_BODY:
...

EMAIL_3_SUBJECT: ...
EMAIL_3_BODY:
..."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    return _parse_sequence(response.content[0].text, dossier, is_enterprise)


def _parse_sequence(text: str, dossier: LeadDossier, is_enterprise: bool) -> OutreachSequence:
    emails = {"1": {"subject": "", "body": ""}, "2": {"subject": "", "body": ""},
              "3": {"subject": "", "body": ""}}
    current_email = None
    current_field = None
    body_lines: list[str] = []

    for line in text.split("\n"):
        for n in ("1", "2", "3"):
            if line.startswith(f"EMAIL_{n}_SUBJECT:"):
                if current_email and current_field == "body":
                    emails[current_email]["body"] = "\n".join(body_lines).strip()
                    body_lines = []
                current_email = n
                current_field = "subject"
                emails[n]["subject"] = line.split(":", 1)[1].strip()
                continue
            if line.startswith(f"EMAIL_{n}_BODY:"):
                if current_email and current_field == "body":
                    emails[current_email]["body"] = "\n".join(body_lines).strip()
                    body_lines = []
                current_email = n
                current_field = "body"
                body_lines = []
                continue
        if current_field == "body":
            body_lines.append(line)

    if body_lines and current_email:
        emails[current_email]["body"] = "\n".join(body_lines).strip()

    def fmt(n: str) -> str:
        s = emails[n]["subject"]
        b = emails[n]["body"]
        return f"Subject: {s}\n\n{b}" if s else b

    return OutreachSequence(
        lead_name=dossier.name,
        company=dossier.company,
        email_1=fmt("1"),
        email_2=fmt("2"),
        email_3=fmt("3"),
        requires_review=is_enterprise,
    )


if __name__ == "__main__":
    from lead_intelligence import LeadDossier

    sample_dossier = LeadDossier(
        name="Sarah Chen", company="Meridian Analytics", title="VP of Sales",
        icp_score=78, icp_tier="high",
        icp_match_reasons=["Series B SaaS", "Hiring for RevOps"],
        company_overview="Meridian Analytics is a B2B SaaS company providing revenue intelligence to mid-market sales teams.",
        likely_pain_points=[
            "SDRs spending 60%+ of time on manual research instead of selling",
            "Inconsistent lead scoring leading to wasted outreach on poor-fit accounts",
        ],
        conversation_hooks=[
            "Meridian posted 3 RevOps roles in the last 30 days — signals scaling the revenue team",
            "Recent G2 review mentions 'our reps spend too much time on data entry'",
        ],
        recommended_sequence="full_outreach",
    )

    seq = generate_outreach_sequence(sample_dossier, is_enterprise=False)

    print(f"Sequence for {seq.lead_name} @ {seq.company}")
    print(f"Requires review: {seq.requires_review}\n")
    print("=== EMAIL 1 (Day 0) ===")
    print(seq.email_1)
    print("\n=== EMAIL 2 (Day 5) ===")
    print(seq.email_2)
    print("\n=== EMAIL 3 (Day 12 — breakup) ===")
    print(seq.email_3)
