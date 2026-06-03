"""
Structured Output — Chapter 4: Prompting and Reasoning Systems

structured_agent_call(prompt, output_schema, system_context) → dict

Appends schema constraint to system prompt.
Retries up to 3× on JSONDecodeError.
Raises ValueError after third failure — caller never sees a raw exception.
"""
import json
import os

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))
MODEL = "claude-sonnet-4-6"


def structured_agent_call(
    prompt: str,
    output_schema: dict,
    system_context: str = "",
    max_retries: int = 3,
) -> dict:
    """
    Call the model and enforce a JSON output schema.

    Args:
        prompt: The user prompt
        output_schema: JSON schema dict the response must match
        system_context: Optional additional system context
        max_retries: Number of retry attempts on parse failure

    Returns:
        Parsed dict matching output_schema

    Raises:
        ValueError: If all retries fail
    """
    schema_instruction = (
        f"CRITICAL: Respond ONLY with valid JSON matching this schema:\n"
        f"{json.dumps(output_schema, indent=2)}\n"
        f"No prose. No explanation. Only the JSON object."
    )
    system = f"{system_context}\n\n{schema_instruction}".strip()

    for attempt in range(max_retries):
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if attempt == max_retries - 1:
                raise ValueError(
                    f"structured_agent_call failed after {max_retries} attempts. "
                    f"Last response: {text[:200]}"
                )
    raise ValueError("structured_agent_call: unreachable")


if __name__ == "__main__":
    schema = {
        "type": "object",
        "properties": {
            "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
            "findings": {"type": "array", "items": {"type": "string"}},
            "recommended_actions": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["risk_level", "findings", "recommended_actions"],
    }

    result = structured_agent_call(
        prompt="Analyze the risk of deploying an AI agent that can send emails autonomously.",
        output_schema=schema,
        system_context="You are a senior security engineer specializing in AI system risk.",
    )
    print(json.dumps(result, indent=2))
