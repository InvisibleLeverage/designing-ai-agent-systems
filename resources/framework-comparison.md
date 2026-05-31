# Agent Framework Comparison

Frameworks for building AI agent systems. Evaluated on: production maturity,
debugging experience, flexibility, operational overhead.

---

## Framework Options

### No Framework (Direct API)
- **Approach:** call Anthropic/OpenAI API directly; write your own loop and dispatch
- **Pros:** full control, no abstraction overhead, easiest to debug
- **Cons:** more boilerplate; reinvent common patterns
- **When to use:** systems where the architecture is well-understood; production systems
  where debugging clarity matters more than scaffolding speed
- **This book's approach:** all examples use direct API calls

### LangChain
- **Pros:** large ecosystem, many integrations, rapid prototyping
- **Cons:** high abstraction overhead, difficult to debug, frequent breaking changes,
  often hides what the model is actually receiving
- **When to use:** prototyping with many integrations; avoid in production-critical systems

### LlamaIndex
- **Pros:** strong RAG primitives, good for document-intensive workflows
- **Cons:** heavy for simple use cases
- **When to use:** RAG-heavy pipelines where document parsing and chunking are the core problem

### Autogen (Microsoft)
- **Pros:** multi-agent conversation patterns out of the box
- **Cons:** conversation-centric model doesn't fit all architectures
- **When to use:** collaborative multi-agent setups with conversation-style coordination

---

## Recommendation

Start with direct API calls. Add a framework only when the boilerplate cost clearly
exceeds the debugging cost of the abstraction. Most production systems are better
served by thin wrappers than by opinionated frameworks.
