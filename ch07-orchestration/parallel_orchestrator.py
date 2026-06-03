"""
Parallel Orchestrator — Chapter 7: Multi-Agent Systems and Orchestration

All agents run simultaneously via asyncio.gather.
One synthesis call merges results into a unified report.
"""
import asyncio
import os
from dataclasses import dataclass

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))
MODEL = "claude-sonnet-4-6"


@dataclass
class AgentSpec:
    id: str
    system_prompt: str
    task: str


class ParallelOrchestrator:
    async def run_parallel(self, agents: list[AgentSpec]) -> dict[str, str]:
        """Run all agents simultaneously. Returns dict[agent_id, output]."""
        results = await asyncio.gather(*[self._run_one(a) for a in agents])
        return {spec.id: result for spec, result in zip(agents, results)}

    async def _run_one(self, agent: AgentSpec) -> str:
        response = await asyncio.to_thread(
            client.messages.create,
            model=MODEL,
            max_tokens=1024,
            system=agent.system_prompt,
            messages=[{"role": "user", "content": agent.task}],
        )
        return response.content[0].text

    def synthesize(self, results: dict[str, str], synthesis_goal: str) -> str:
        """Merge all agent outputs into one coherent report."""
        combined = "\n\n".join(f"[{agent_id}]\n{output}" for agent_id, output in results.items())
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system="Synthesize the following agent outputs into one unified, well-structured report.",
            messages=[{"role": "user", "content": f"{synthesis_goal}\n\n{combined}"}],
        )
        return response.content[0].text


if __name__ == "__main__":
    orchestrator = ParallelOrchestrator()
    companies = ["Salesforce", "HubSpot", "Pipedrive"]
    agents = [
        AgentSpec(
            id=company,
            system_prompt="You are a competitive intelligence analyst.",
            task=f"Summarize {company}'s CRM product: key features, pricing tier, target customer.",
        )
        for company in companies
    ]
    results = asyncio.run(orchestrator.run_parallel(agents))
    report = orchestrator.synthesize(results, "Create a CRM competitive landscape comparison.")
    print(report)
