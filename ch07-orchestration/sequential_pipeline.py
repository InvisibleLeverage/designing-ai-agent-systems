"""
Sequential Pipeline — Chapter 7: Multi-Agent Systems and Orchestration

Each stage's output feeds the next as input.
Fail-fast: a stage returning an error stops the pipeline.
"""
import os
from dataclasses import dataclass
from typing import Callable

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))
MODEL = "claude-sonnet-4-6"


@dataclass
class PipelineStage:
    name: str
    system_prompt: str
    input_transformer: Callable[[str], str] = lambda x: x
    output_transformer: Callable[[str], str] = lambda x: x


class SequentialPipeline:
    def __init__(self, stages: list[PipelineStage]):
        self.stages = stages

    def run(self, initial_input: str) -> dict:
        """Run all stages in order. Returns final output and per-stage trace."""
        current = initial_input
        trace = []

        for stage in self.stages:
            prompt = stage.input_transformer(current)
            response = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=stage.system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            output = stage.output_transformer(response.content[0].text)
            trace.append({"stage": stage.name, "output": output})
            current = output

        return {"final": current, "trace": trace}


if __name__ == "__main__":
    pipeline = SequentialPipeline([
        PipelineStage(
            name="research",
            system_prompt="Research the topic and extract key facts. Be concise.",
        ),
        PipelineStage(
            name="analysis",
            system_prompt="Analyze the research findings. Identify the 3 most important insights.",
        ),
        PipelineStage(
            name="report",
            system_prompt="Write a 3-paragraph executive summary based on the analysis.",
        ),
    ])

    result = pipeline.run("The current state of AI agent deployment in enterprise software.")
    print("Final Report:")
    print(result["final"])
