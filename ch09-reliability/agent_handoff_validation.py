"""
Agent Handoff Validation — Chapter 9: System Reliability and Safety

Use at every inter-agent handoff in multi-agent pipelines.
A fast Haiku call checks: required fields present? format correct? obvious contradictions?

Cost: ~$0.001 per handoff — far cheaper than debugging cascade failures.
"""
import json
import os

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
HAIKU = "claude-haiku-4-5-20251001"

VALIDATION_SYSTEM = """You are a schema validator. Given an output and expected schema,
check: (1) are all required fields present? (2) are there obvious format errors?
(3) are there obvious logical contradictions?
Return ONLY this JSON:
{"valid": bool, "issues": ["list"], "confidence": 0.0-1.0, "proceed": bool}"""


def validate_agent_handoff(
    output: str,
    expected_schema: dict,
    stage_name: str = "unknown",
) -> dict:
    """
    Validate an agent's output before passing it to the next stage.

    Returns: {"valid": bool, "issues": list, "confidence": float, "proceed": bool}
    proceed=False → halt the pipeline at this stage.
    """
    prompt = (
        f"Stage: {stage_name}\n"
        f"Expected schema:\n{json.dumps(expected_schema, indent=2)}\n\n"
        f"Output to validate:\n{output}"
    )
    try:
        response = client.messages.create(
            model=HAIKU,
            max_tokens=512,
            system=VALIDATION_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        return {
            "valid":      False,
            "issues":     ["Validation call returned unparseable response"],
            "confidence": 0.0,
            "proceed":    False,
        }
