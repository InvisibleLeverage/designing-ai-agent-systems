# Designing AI Agent Systems

> Companion repository for the book **Designing AI Agent Systems: A Practical Guide to Multi-Agent Architectures, Autonomous Workflows, and Intelligent AI Applications** by Akshay Panda.

This repository contains the code examples, prompt templates, architecture diagrams, deployment templates, and companion resources referenced throughout the book. Each folder maps directly to a chapter so you can follow along as you read.

---

## Quick start

```bash
git clone https://github.com/InvisibleLeverage/designing-ai-agent-systems
cd designing-ai-agent-systems
pip install -r requirements.txt
```

Most resources in this repository — diagrams, prompts, templates, and reference materials — can be used without an API key.

To run the code examples that call an LLM:

```bash
export ANTHROPIC_API_KEY=your_key_here
python ch03-agent-architectures/agent_loop.py
```

---

## What's in this repository

| Folder | Content |
|---|---|
| `ch03-agent-architectures/` | Goal parser, agent loop, tool library, parallel fan-out |
| `ch04-prompting-reasoning/` | Structured output, role prompts, three-pass reflection |
| `ch05-memory-systems/` | Context manager, session memory, vector memory |
| `ch06-tool-systems/` | Tool registry, tool dispatcher, schema validation |
| `ch07-orchestration/` | Sequential pipeline, parallel orchestrator, hierarchical orchestrator |
| `ch09-reliability/` | Circuit breaker, output validator, loop detector, handoff validation |
| `ch11-economics/` | Cost-guarded task runner |
| `prompts/` | Production system prompt templates for research, orchestration, and content agents |
| `templates/` | Architecture and deployment templates — goal parser, memory schema, runbooks |
| `resources/` | Framework comparisons, vector database comparison, recommended tools |
| `diagrams/` | Architecture diagrams referenced in the book |

---

## Repository structure

```
designing-ai-agent-systems/
├── ch03-agent-architectures/
│   ├── agent_loop.py
│   ├── goal_parser.py
│   ├── tool_library.py
│   └── parallel_fanout.py
├── ch04-prompting-reasoning/
│   ├── structured_output.py
│   ├── role_prompts.py
│   └── reflection.py
├── ch05-memory-systems/
│   ├── context_manager.py
│   ├── session_memory.py
│   └── vector_memory.py
├── ch06-tool-systems/
│   ├── tool_registry.py
│   └── tool_dispatcher.py
├── ch07-orchestration/
│   ├── sequential_pipeline.py
│   ├── parallel_orchestrator.py
│   └── hierarchical_orchestrator.py
├── ch09-reliability/
│   ├── circuit_breaker.py
│   ├── output_validator.py
│   ├── loop_detector.py
│   ├── validated_memory_store.py
│   └── agent_handoff_validation.py
├── ch11-economics/
│   └── cost_guard.py
├── prompts/
│   ├── orchestrator.txt
│   ├── research-agent.txt
│   ├── content-agent.txt
│   ├── fact-checker.txt
│   ├── reflection.txt
│   └── reviewer.txt
├── templates/
│   ├── goal-parser-template.md
│   ├── memory-schema-template.md
│   ├── research-agent-template.md
│   ├── tool-registry-template.md
│   ├── deployment-runbook.md
│   └── production-checklist.md
├── resources/
│   ├── framework-comparison.md
│   ├── vector-database-comparison.md
│   └── recommended-tools.md
├── diagrams/
├── requirements.txt
├── LICENSE
└── CONTRIBUTING.md
```

---

## How to use this repository with the book

Each chapter folder contains the runnable implementation contracts described in that chapter. The pattern is the same throughout:

1. Read the chapter to understand the architecture and design decisions
2. Open the corresponding folder in this repository
3. Run the implementation to see it working
4. Adapt it to your own use case

The `prompts/` and `templates/` folders are standalone — use them directly in your own projects without reading the book first.

---

## Who this is for

- Engineers building production AI agent systems
- Architects evaluating multi-agent patterns
- Technical founders designing autonomous workflows
- AI practitioners moving from prototypes to production

---

## Book chapters

| Part | Chapters |
|---|---|
| **Part I — Foundations** | Ch 1: The Rise of Agentic AI · Ch 2: What Makes an AI System Agentic · Ch 3: Designing AI Agent Architectures |
| **Part II — Building Intelligent Agent Systems** | Ch 4: Prompting and Reasoning · Ch 5: Memory Systems · Ch 6: Tool Systems · Ch 7: Orchestration |
| **Part III — Production Engineering** | Ch 8: Deployment and Scaling · Ch 9: Reliability and Safety · Ch 10: Observability · Ch 11: Economics |
| **Part IV — Real-World Agent Systems** | Ch 12: Research Agents · Ch 13: Content Systems · Ch 14: Business Automation · Ch 15: Productivity |

---

## License

MIT — see [LICENSE](LICENSE)
