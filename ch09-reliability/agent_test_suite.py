"""
Agent Test Suite — Chapter 9: System Reliability and Safety

Behavioral testing for AI agent systems. Tests at the goal level, not the output level:
"Did the agent accomplish the goal?" not "Did the output match a string?"

Uses an LLM judge (Haiku) to evaluate outputs against success/failure criteria.
"""
import os
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


@dataclass
class AgentTestCase:
    name:              str
    goal:              str
    success_criteria:  list[str]   # what must be true for the test to pass
    failure_criteria:  list[str]   # if any of these are true, the test fails
    max_steps:         int   = 20
    timeout_s:         int   = 120
    tags:              list[str] = field(default_factory=list)


@dataclass
class TestResult:
    test:                  AgentTestCase
    passed:                bool
    duration_s:            float
    quality_score:         float          # 0.0 – 1.0
    success_criteria_met:  list[str]
    failure_criteria_hit:  list[str]
    agent_output:          str
    judge_reasoning:       str
    error:                 str = ""


class AgentTestSuite:
    """
    Runs behavioral tests against an agent. Agent is a callable: (goal, max_steps) → str.
    LLM judge (Haiku) evaluates outputs — cheap, fast, consistent.
    """

    def __init__(self, agent_runner: Callable[[str, int], str]):
        self._runner = agent_runner

    def run_test(self, test_case: AgentTestCase) -> TestResult:
        """Run a single test case. Returns a TestResult regardless of pass/fail."""
        start = time.time()

        # Run the agent
        try:
            output = self._runner(test_case.goal, test_case.max_steps)
        except Exception as exc:
            return TestResult(
                test=test_case, passed=False,
                duration_s=round(time.time() - start, 2),
                quality_score=0.0, success_criteria_met=[],
                failure_criteria_hit=["agent raised an exception"],
                agent_output="", judge_reasoning="", error=str(exc),
            )

        # LLM judge evaluation
        judge_result = self._judge(test_case, output)
        duration     = round(time.time() - start, 2)

        return TestResult(
            test=test_case,
            passed=judge_result["passed"],
            duration_s=duration,
            quality_score=judge_result.get("overall_quality", 0.0),
            success_criteria_met=judge_result.get("success_criteria_met", []),
            failure_criteria_hit=judge_result.get("failure_criteria_hit", []),
            agent_output=output,
            judge_reasoning=judge_result.get("reasoning", ""),
        )

    def run_all(self, test_cases: list[AgentTestCase]) -> dict:
        """Run all test cases. Returns summary + individual results."""
        results = [self.run_test(tc) for tc in test_cases]
        passed  = sum(1 for r in results if r.passed)
        return {
            "total":     len(results),
            "passed":    passed,
            "failed":    len(results) - passed,
            "pass_rate": f"{passed/len(results):.0%}" if results else "0%",
            "results":   results,
        }

    def _judge(self, test_case: AgentTestCase, output: str) -> dict:
        success_list = "\n".join(f"  - {c}" for c in test_case.success_criteria)
        failure_list = "\n".join(f"  - {c}" for c in test_case.failure_criteria)

        prompt = (
            f"Evaluate this AI agent output against the test criteria.\n\n"
            f"GOAL: {test_case.goal}\n\n"
            f"AGENT OUTPUT:\n{output[:2000]}\n\n"
            f"SUCCESS CRITERIA (all must be met to pass):\n{success_list}\n\n"
            f"FAILURE CRITERIA (any one fails the test):\n{failure_list}\n\n"
            f"Respond in JSON:\n"
            f'{{"passed": true/false, "overall_quality": 0.0-1.0, '
            f'"success_criteria_met": [...], "failure_criteria_hit": [...], '
            f'"reasoning": "one sentence"}}'
        )

        import json
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"passed": False, "overall_quality": 0.0,
                    "success_criteria_met": [], "failure_criteria_hit": [],
                    "reasoning": "judge parse error"}


# ── Quick smoke test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    def mock_agent(goal: str, max_steps: int) -> str:
        return f"I have completed the task: {goal}. The answer is 42. Sources: none."

    suite = AgentTestSuite(agent_runner=mock_agent)

    test_cases = [
        AgentTestCase(
            name="basic_completion",
            goal="What is 2 + 2?",
            success_criteria=["Output contains a numeric answer", "Response is concise"],
            failure_criteria=["Output is empty", "Output contains error message"],
        ),
        AgentTestCase(
            name="source_citation",
            goal="Summarise the latest AI news",
            success_criteria=["Output contains a summary", "Output cites at least one source"],
            failure_criteria=["Output contains no factual claims", "Output is empty"],
        ),
    ]

    summary = suite.run_all(test_cases)
    print(f"Results: {summary['passed']}/{summary['total']} passed ({summary['pass_rate']})")
    for r in summary["results"]:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.test.name} — quality: {r.quality_score:.2f} — {r.duration_s}s")
        print(f"         {r.judge_reasoning}")
