# Goal Parser Template

Use this template to define how your agent parses incoming goals.

## System Prompt

```
Parse the following goal into a structured execution plan. Return strict JSON:
{
  "requires_clarification": bool,
  "clarification_questions": [],
  "clarified_goal": "precise restatement",
  "subtasks": ["ordered list of single-step actions"],
  "success_criteria": ["measurable completion conditions"],
  "estimated_steps": integer
}
```

## Clarification Triggers

Add these conditions to require human clarification before execution:

- [ ] Goal involves financial transactions > $__
- [ ] Goal involves sending external communications
- [ ] Goal requires accessing systems outside the defined scope
- [ ] Goal is ambiguous in more than one critical dimension

## Subtask Ordering Rules

1. Information gathering before synthesis
2. Read operations before write operations
3. Validation before irreversible actions
4. Reversible steps before irreversible steps

## Success Criteria Format

Good: "Research report contains at least 3 verified competitor pricing data points"
Bad:  "Research is complete"

Good: "All required JSON fields are populated and non-null"
Bad:  "Output looks good"
