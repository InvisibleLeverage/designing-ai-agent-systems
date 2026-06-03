# Designing AI Agent Systems

> Companion repository for the book **Designing AI Agent Systems: A Practical Guide to Multi-Agent Architectures, Autonomous Workflows, and Intelligent AI Applications** by Akshay Panda.

This repository contains the production-quality code examples referenced throughout the book. Each chapter folder maps directly to a book chapter so you can follow along as you read.

---

## Quick start

```bash
git clone https://github.com/InvisibleLeverage/designing-ai-agent-systems
cd designing-ai-agent-systems
pip install -r requirements.txt
export AI_API_KEY=your_key_here
python ch03-agent-architectures/agent_loop.py
```

---

## What's in this repository

### Chapter implementations

| Folder | Chapter | Content |
|---|---|---|
| `ch03-agent-architectures/` | Ch 3: Agent Architectures | Goal parser, agent loop, tool library, parallel fan-out, parallel orchestrator |
| `ch04-prompting-reasoning/` | Ch 4: Prompting & Reasoning | Structured output, role prompts, three-pass reflection |
| `ch05-memory-systems/` | Ch 5: Memory Systems | Context manager, session memory, vector memory |
| `ch06-tool-systems/` | Ch 6: Tool Systems | Tool registry, tool dispatcher, tool library (definitions + dispatch) |
| `ch07-orchestration/` | Ch 7: Orchestration | Sequential pipeline, parallel orchestrator, hierarchical orchestrator, message bus, task queue, call timeout |
| `ch08-deployment/` | Ch 8: Deployment & Scaling | FastAPI agent service, cost manager, token budget, model router, circuit breaker, tool cache |
| `ch09-reliability/` | Ch 9: Reliability & Safety | Circuit breaker, output validator, loop detector, handoff validation, test suite, evaluator, retry backoff, task graph, confidence routing |
| `ch10-observability/` | Ch 10: Observability | Agent tracer, quality monitor, retrieval health |
| `ch11-economics/` | Ch 11: Economics | Cost guard, loop detector, injection sanitiser, context management |
| `ch12-research/` | Ch 12: Research Agents | RAG research system, document intelligence pipeline |
| `ch13-content/` | Ch 13: Content Systems | Content multiplier (5 platform formats), publishing calendar |
| `ch14-automation/` | Ch 14: Business Automation | CRM intelligence, AI proposal generator |

### Production blueprints

End-to-end deployable systems from Part IV of the book.

| Folder | Blueprint | Description |
|---|---|---|
| `blueprint-sdr/` | Blueprint 1: AI SDR | Lead intelligence, outreach sequence, engagement monitor |
| `blueprint-research-pipeline/` | Blueprint 2: Research Pipeline | Decompose → parallel agents → synthesis → verification flags |
| `blueprint-content-studio/` | Blueprint 3: Content Studio | Brief → parallel section writing → edit → channel adaptation |
| `blueprint-finance-analyst/` | Blueprint 4: Finance Analyst | Earnings transcript → structured metrics → beat/miss → risk |
| `blueprint-enterprise-sales/` | Blueprint 5: Enterprise Sales | Qualify → research → personalised outreach → nurture cadence |
| `blueprint-research-pipeline-production/` | Blueprint 6: Production Research | Source cache + semantic memory + per-claim confidence scores |
| `blueprint-content-media-system/` | Blueprint 7: Content Media System | Full pipeline + topic intelligence feedback loop |

### Supporting resources

| Folder | Content |
|---|---|
| `prompts/` | Production system prompt templates for research, orchestration, and content agents |
| `templates/` | Architecture and deployment templates — goal parser, memory schema, runbooks |
| `resources/` | Framework comparisons, vector database comparison, recommended tools |

---

## Repository structure

```
designing-ai-agent-systems/
├── ch03-agent-architectures/
│   ├── agent_loop.py
│   ├── goal_parser.py
│   ├── tool_library.py
│   ├── parallel_fanout.py
│   └── parallel_orchestrator.py
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
│   ├── tool_dispatcher.py
│   └── tool_library.py
├── ch07-orchestration/
│   ├── sequential_pipeline.py
│   ├── parallel_orchestrator.py
│   ├── hierarchical_orchestrator.py
│   ├── message_bus.py
│   ├── task_queue.py
│   └── call_timeout.py
├── ch08-deployment/
│   ├── fastapi_agent_service.py
│   ├── cost_manager.py
│   ├── token_budget_manager.py
│   ├── model_router.py
│   ├── circuit_breaker.py
│   └── tool_cache.py
├── ch09-reliability/
│   ├── circuit_breaker.py
│   ├── output_validator.py
│   ├── loop_detector.py
│   ├── validated_memory_store.py
│   ├── agent_handoff_validation.py
│   ├── agent_test_suite.py
│   ├── agent_evaluator.py
│   ├── retry_backoff.py
│   ├── task_graph.py
│   └── confidence_routing.py
├── ch10-observability/
│   ├── agent_tracer.py
│   ├── quality_monitor.py
│   └── retrieval_health.py
├── ch11-economics/
│   ├── cost_guard.py
│   ├── loop_detector.py
│   ├── injection_sanitiser.py
│   └── context_management.py
├── ch12-research/
│   ├── rag_research_system.py
│   └── document_intelligence.py
├── ch13-content/
│   ├── content_multiplier.py
│   └── content_publisher.py
├── ch14-automation/
│   ├── crm_intelligence.py
│   └── proposal_generator.py
├── blueprint-sdr/
│   ├── lead_intelligence.py
│   ├── outreach_sequence.py
│   └── engagement_monitor.py
├── blueprint-research-pipeline/
│   └── research_pipeline.py
├── blueprint-content-studio/
│   └── content_studio.py
├── blueprint-finance-analyst/
│   └── finance_analyst.py
├── blueprint-enterprise-sales/
│   └── enterprise_sales.py
├── blueprint-research-pipeline-production/
│   └── production_research.py
├── blueprint-content-media-system/
│   └── content_media_system.py
├── prompts/
├── templates/
├── resources/
├── requirements.txt
├── LICENSE
└── CONTRIBUTING.md
```

---

## How to use this repository with the book

Each chapter folder contains the runnable implementation contracts described in that chapter:

1. Read the chapter to understand the architecture and design decisions
2. Open the corresponding folder in this repository
3. Run the implementation to see it working
4. Adapt it to your own use case

The blueprint folders contain end-to-end systems from Part IV. Each is self-contained — read the folder's README for setup instructions.

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
| **Part II — Building Blocks** | Ch 4: Prompting and Reasoning · Ch 5: Memory Systems · Ch 6: Tool Systems · Ch 7: Orchestration |
| **Part III — Production Engineering** | Ch 8: Deployment and Scaling · Ch 9: Reliability and Safety · Ch 10: Observability · Ch 11: Economics |
| **Part IV — Real-World Systems** | Ch 12: Research Agents · Ch 13: Content Systems · Ch 14: Business Automation · Ch 15: Productivity · Ch 16: Engineering at the Edge |

---

## License

MIT — see [LICENSE](LICENSE)
