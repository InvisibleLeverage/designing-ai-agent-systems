"""
Output Validator — Chapter 9: System Reliability and Safety

Two-stage output validation:
  1. Structural checks (length, uncertainty language)
  2. Grounding check via Haiku (are claims supported by source context?)

Use on any output that will be delivered to users or stored as fact.
"""
import os
import re

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))
HAIKU = "claude-haiku-4-5-20251001"   # fast, cheap — appropriate for validation calls

UNCERTAINTY_PATTERNS = [
    r"\bI think\b", r"\bprobably\b", r"\bmight be\b",
    r"\bI'm not sure\b", r"\bcould be\b", r"\bpossibly\b",
]

GROUNDING_SYSTEM = """You are a fact-checker. Given a response and its source context,
check whether all factual claims in the response are supported by the source context.
Return JSON: {"grounding_score": 0.0-1.0, "unsupported_claims": ["list of claims not in source"]}
Output only valid JSON."""


def validate_output(output: str, source_context: str) -> dict:
    """
    Validate output quality and grounding.
    Returns: {"valid": bool, "issues": list[str], "grounding_score": float}
    """
    issues = []

    # Stage 1: Structural checks
    if len(output.strip()) < 50:
        issues.append("Output too short — likely incomplete.")

    for pattern in UNCERTAINTY_PATTERNS:
        if re.search(pattern, output, re.IGNORECASE):
            issues.append(f"Uncertainty language detected: matches '{pattern}'")
            break

    # Stage 2: Grounding check (Haiku — fast and cheap)
    grounding_score = 1.0
    if source_context:
        response = client.messages.create(
            model=HAIKU,
            max_tokens=512,
            system=GROUNDING_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"Source context:\n{source_context}\n\nResponse to check:\n{output}",
            }],
        )
        import json
        data = json.loads(response.content[0].text)
        grounding_score = data.get("grounding_score", 1.0)
        for claim in data.get("unsupported_claims", []):
            issues.append(f"Unsupported claim: {claim}")

    return {
        "valid":           grounding_score >= 0.6 and len(issues) == 0,
        "issues":          issues,
        "grounding_score": grounding_score,
    }
