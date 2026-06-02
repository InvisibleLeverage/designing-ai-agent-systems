"""
Proposal Generator — Chapter 14: AI Business Automation Systems

Generates a structured proposal document from a project brief.
Target: 90% draft in ~5 minutes. Always human-review before sending.

Eight-section structure:
  1. Executive Summary
  2. Understanding the Challenge
  3. Proposed Approach
  4. Scope of Work
  5. Timeline
  6. Investment
  7. Why Choose Us
  8. Next Steps
"""
import os
from dataclasses import dataclass
from typing import Optional

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


@dataclass
class ProjectBrief:
    client_name:    str
    project_scope:  str
    timeline:       str
    budget_range:   str
    our_strengths:  list[str]
    industry:       Optional[str] = None
    pain_points:    Optional[str] = None
    success_metrics: Optional[str] = None


def generate_proposal(brief: ProjectBrief) -> str:
    """
    Generate a full proposal document from a ProjectBrief.
    Returns the complete proposal as a formatted string.

    Review checklist before sending:
      □ All figures and timelines confirmed internally
      □ Client-specific context added (political dynamics, prior conversations)
      □ Pricing approved by stakeholder
      □ Competitive positioning checked against known alternatives
    """
    strengths_formatted = "\n".join(f"- {s}" for s in brief.our_strengths)

    prompt = f"""Write a professional business proposal for {brief.client_name}.

PROJECT DETAILS:
- Scope: {brief.project_scope}
- Timeline: {brief.timeline}
- Budget range: {brief.budget_range}
- Industry: {brief.industry or 'Not specified'}
- Key pain points: {brief.pain_points or 'Not specified'}
- Success metrics: {brief.success_metrics or 'Not specified'}

OUR STRENGTHS:
{strengths_formatted}

Write the proposal with exactly these eight sections in order:

1. EXECUTIVE SUMMARY
Brief overview of the engagement, the core problem we are solving, and the expected business outcome. 2–3 paragraphs.

2. UNDERSTANDING THE CHALLENGE
Demonstrate that we understand the client's situation, constraints, and goals. Reference their specific industry and pain points. 2–3 paragraphs.

3. PROPOSED APPROACH
Our methodology and how we will solve their problem. Include our reasoning for key decisions. 2–3 paragraphs.

4. SCOPE OF WORK
Present as a table with columns: Deliverable | Description | Timeline. Include 4–6 specific deliverables.

5. TIMELINE
A phased breakdown. Present as: Phase 1 (weeks 1–N): [activities]. Phase 2, etc.

6. INVESTMENT
The investment range, what is included, and payment structure. Be clear about what is and is not in scope.

7. WHY CHOOSE US
3–5 bullet points connecting our specific strengths to their specific needs.

8. NEXT STEPS
Clear, numbered actions for both parties. Include a proposed kickoff date placeholder.

Tone: confident and professional, not salesy. Demonstrate competence through specificity.
Format each section with a bold header."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=6_000,
        messages=[{"role": "user", "content": prompt}],
    )

    proposal_body = response.content[0].text.strip()

    header = (
        f"PROPOSAL FOR {brief.client_name.upper()}\n"
        f"{'=' * 60}\n"
        f"Project: {brief.project_scope}\n"
        f"Prepared by: [Your Company Name]\n"
        f"Date: [Insert date]\n"
        f"{'=' * 60}\n\n"
        f"⚠️  DRAFT — Human review required before sending\n\n"
    )

    return header + proposal_body


def generate_proposal_variants(brief: ProjectBrief, n_variants: int = 3) -> list[str]:
    """
    Generate N executive summary variants for A/B testing messaging.
    Useful when positioning strategy is uncertain.
    """
    strengths_formatted = "\n".join(f"- {s}" for s in brief.our_strengths)
    prompt = (
        f"Write {n_variants} different executive summary variants for a proposal to "
        f"{brief.client_name}.\n\n"
        f"Project scope: {brief.project_scope}\n"
        f"Pain points: {brief.pain_points or 'not specified'}\n"
        f"Our strengths:\n{strengths_formatted}\n\n"
        f"Each variant should lead with a different angle:\n"
        f"  Variant 1: Lead with the business outcome / ROI\n"
        f"  Variant 2: Lead with the risk of inaction\n"
        f"  Variant 3: Lead with our unique capability\n\n"
        f"Separate each variant with '---'. Label each VARIANT 1 / 2 / 3.\n"
        f"Each variant: 2 short paragraphs only."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2_048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    return [v.strip() for v in raw.split("---") if v.strip()]


# ── Quick smoke test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    brief = ProjectBrief(
        client_name   = "Meridian Financial",
        project_scope = "Build an AI-powered research agent to automate equity analysis and "
                        "generate weekly sector briefings for the investment team",
        timeline      = "12 weeks",
        budget_range  = "$80,000 – $120,000",
        our_strengths = [
            "Three completed AI agent deployments in financial services",
            "In-house expertise in RAG architecture and hallucination mitigation",
            "Production-proven reliability patterns (99.2% uptime across client deployments)",
            "Dedicated post-launch support for 90 days",
        ],
        industry        = "Financial services / asset management",
        pain_points     = "Analysts spend 60% of their time gathering and formatting data "
                          "rather than generating investment insight",
        success_metrics = "Reduce research preparation time by 70%, weekly briefings "
                          "delivered by 8 AM Monday without manual effort",
    )

    proposal = generate_proposal(brief)
    print(proposal[:1500])
    print("\n... [truncated for display — full proposal generated]")
    print(f"\nTotal characters: {len(proposal)}")
