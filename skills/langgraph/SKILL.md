---
name: langgraph
description: Reference skill for building stateful, multi-step LLM agents with LangGraph and LangChain — graphs, state, nodes/edges, tool calling, persistence/checkpointing, human-in-the-loop, and the deepagents scaffolding. Load this for any agent-orchestration or LangGraph query.
metadata:
  type: reference
  framework: langgraph
  ecosystem: langchain
---

# LangGraph Skill

Context for designing and implementing agents with **LangGraph** (the graph runtime under
LangChain) and the **deepagents** package used in this project. Use it whenever a task
involves agent orchestration, state machines over LLMs, tool-calling loops, or
persistence/human-in-the-loop.

## When to use this skill

- Building or modifying an agent graph (nodes, edges, conditional routing).
- Designing the shared **state** that flows through a graph.
- Adding tool calling, sub-agents, checkpointing, streaming, or human approval.
- Working with `deepagents` (planning + virtual FS + sub-agents scaffolding).

## Mental model

LangGraph models an agent as a **directed graph of nodes over a shared state object**.

- **State** — a typed dict (often `TypedDict`) holding everything the run needs. Each node
  returns a partial update that is merged in. Use **reducers** (e.g. `add_messages`) to
  control how a key is combined rather than overwritten.
- **Nodes** — plain functions `(state) -> partial_state`. A node can call an LLM, a tool,
  or arbitrary code.
- **Edges** — wiring between nodes. **Normal edges** are fixed; **conditional edges** route
  based on a function of the state (this is how you build loops and branching).
- **Compile** the `StateGraph` into a runnable, optionally with a **checkpointer** for
  persistence and a `thread_id` for per-conversation memory.

## Key capabilities

| Capability         | How                                                            |
|--------------------|---------------------------------------------------------------|
| Memory/persistence | Compile with a checkpointer (`MemorySaver`, sqlite, postgres) |
| Resume / time-travel | Checkpoints keyed by `thread_id` in the config              |
| Tool calling       | `ToolNode` + conditional edge back to the LLM node            |
| Streaming          | `graph.stream(...)` / `astream` with `stream_mode`            |
| Human-in-the-loop  | `interrupt()` / `interrupt_before` on a node, then resume     |
| Prebuilt agent     | `create_react_agent(model, tools)`                            |

## deepagents in this project

`deepagents` builds on LangGraph to provide the four deep-agent capabilities:
explicit **planning** (todo tool), a **virtual file system** (read/write files),
**sub-agents** (delegated isolated contexts), and a **detailed system prompt**.
Prefer `create_deep_agent(tools, instructions, subagents=...)` for long-horizon tasks.

## Cross-references

- `instruction.md` — quick build checklist.
- `instructions.md` — detailed how-to and design decisions.
- `examples.md` — runnable graph patterns.
