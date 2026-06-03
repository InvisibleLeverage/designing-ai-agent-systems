"""
FastAPI Agent Service — Chapter 8: Deployment and Scaling

Task lifecycle: queued → running → completed | failed | timeout

Four components:
  1. Typed request/response models
  2. In-memory task store (swap for Redis/Postgres in production)
  3. Background executor that runs the agent loop
  4. REST endpoints: POST /tasks, GET /tasks/{id}, GET /health
"""
import asyncio
import os
import time
import uuid
from contextlib import asynccontextmanager
from enum import Enum
from typing import Optional

import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

client = anthropic.Anthropic(api_key=os.environ.get("AI_API_KEY"))


# ─── Task models ────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    QUEUED    = "queued"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    TIMEOUT   = "timeout"


class TaskRequest(BaseModel):
    goal:       str
    user_id:    str
    priority:   int = 5          # 1 = highest, 10 = lowest
    max_steps:  int = 20
    model:      str = "claude-sonnet-4-6"


class TaskResponse(BaseModel):
    task_id:     str
    status:      TaskStatus
    result:      Optional[str] = None
    error:       Optional[str] = None
    steps_taken: int = 0
    tokens_used: int = 0
    started_at:  Optional[float] = None
    completed_at: Optional[float] = None


# ─── In-memory task store (replace with Redis/Postgres for production) ───────

_tasks: dict[str, TaskResponse] = {}


# ─── Minimal tool library for the background executor ────────────────────────

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information. Use for factual queries and recent events.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    }
]


def dispatch_tool(name: str, inputs: dict) -> dict:
    if name == "web_search":
        return {"result": f"[web_search stub] Results for: {inputs.get('query', '')}"}
    return {"error": f"Unknown tool: {name}"}


# ─── Background agent executor ───────────────────────────────────────────────

async def _run_agent(task_id: str, request: TaskRequest) -> None:
    task = _tasks[task_id]
    task.status     = TaskStatus.RUNNING
    task.started_at = time.time()

    messages  = [{"role": "user", "content": request.goal}]
    step      = 0
    total_tok = 0

    try:
        while step < request.max_steps:
            step += 1
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.messages.create(
                    model=request.model,
                    max_tokens=4096,
                    system="You are a helpful AI agent. Use available tools when needed. "
                           "Complete the task and provide a clear final answer.",
                    tools=TOOLS,
                    messages=messages,
                ),
            )

            total_tok += response.usage.input_tokens + response.usage.output_tokens
            task.steps_taken = step
            task.tokens_used = total_tok

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        task.result = block.text
                task.status       = TaskStatus.COMPLETED
                task.completed_at = time.time()
                return

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = dispatch_tool(block.name, block.input)
                        tool_results.append({
                            "type":        "tool_result",
                            "tool_use_id": block.id,
                            "content":     str(result),
                        })
                messages.append({"role": "user", "content": tool_results})

        # Step limit reached
        task.status       = TaskStatus.TIMEOUT
        task.completed_at = time.time()

    except Exception as exc:
        task.status       = TaskStatus.FAILED
        task.error        = str(exc)
        task.completed_at = time.time()


# ─── App ─────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="AI Agent Service", lifespan=lifespan)


@app.post("/tasks", response_model=TaskResponse, status_code=202)
async def submit_task(request: TaskRequest, background_tasks=None):
    task_id = str(uuid.uuid4())
    _tasks[task_id] = TaskResponse(task_id=task_id, status=TaskStatus.QUEUED)
    asyncio.create_task(_run_agent(task_id, request))
    return _tasks[task_id]


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return _tasks[task_id]


@app.get("/health")
async def health():
    counts = {}
    for t in _tasks.values():
        counts[t.status] = counts.get(t.status, 0) + 1
    return {"status": "ok", "tasks": counts}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
