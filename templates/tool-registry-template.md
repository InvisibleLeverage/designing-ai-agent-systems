# Tool Registry Template

## Tool Definition Checklist

For each tool, complete this before registering:

```python
{
    "name": "descriptive_verb_noun",   # e.g. "search_web", "read_document"
    "description": """
        WHEN to use this tool:
        [1-2 sentences describing the specific situation that calls for this tool]

        WHAT the output looks like:
        [format, typical content, size range]

        WARNING (if applicable):
        [non-idempotent, rate-limited, irreversible — state explicitly]
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "param_name": {
                "type": "string",
                "description": "precise description of what this parameter does"
            }
        },
        "required": ["param_name"]
    }
}
```

## Tool Error Contract

Every tool handler MUST return `{"error": "..."}` on failure. Never:
- Raise an exception (agent cannot catch it)
- Return empty string (agent interprets as success)
- Return None (breaks JSON serialization)

## Pre-Registration Checklist

- [ ] Description answers: WHEN, WHAT output looks like, and WARNING if applicable
- [ ] Input schema has descriptions for every parameter
- [ ] Handler returns `{"error": "..."}` on all failure paths
- [ ] Non-idempotent tools are marked in description AND in non_idempotent registry
- [ ] Tool tested in isolation before integration
- [ ] Rate limits documented and circuit breaker configured if applicable
