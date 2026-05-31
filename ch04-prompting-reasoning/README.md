# Chapter 4 — Prompting and Reasoning Systems

Six patterns that separate deployed agents from demo agents.

## Files

| File | Contract | Description |
|---|---|---|
| `structured_output.py` | Structured Output | JSON-schema-enforced agent calls with retry |
| `role_prompts.py` | Role Prompt Anatomy | Identity + priorities + output structure |
| `reflection.py` | Three-Pass Reflection | Draft → critique → revise loop |

## Key principle

> The system prompt is not a request — it is a specification.
> Agents with well-designed system prompts behave predictably at 10,000 tasks.
