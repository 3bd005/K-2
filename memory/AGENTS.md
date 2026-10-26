# Agents.md

Context file for **K-2**, loaded into its deep agents on invocation. Captures the
architecture, conventions, and operating principles these agents rely on. Keep it current
as the system evolves.

## What is a Deep Agent?

A "deep agent" is an LLM-driven agent designed for **long-horizon, multi-step tasks** rather
than single request/response turns. It goes beyond a simple tool-calling loop by combining four
capabilities that let it stay coherent over many steps:

1. **Explicit planning** — the agent writes and maintains a plan (e.g. a to-do list) so it can
   track progress, re-prioritize, and recover from detours instead of losing the thread.
2. **A persistent file system / workspace** — intermediate results, notes, and artifacts are
   written to files (the "virtual file system") instead of being held only in context. This
   offloads memory and keeps the context window focused.
3. **Sub-agents (delegation)** — the orchestrator spawns specialized child agents for isolated
   sub-tasks. Each runs with its own clean context and returns only the conclusion, keeping the
   parent's context lean.
4. **A detailed system prompt** — rich, opinionated instructions that encode how to plan, when
   to delegate, and how to use tools. This is the single biggest lever on agent quality.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                     Orchestrator Agent                     │
│   (system prompt + planning + tool loop + context mgmt)    │
└───────┬───────────────┬──────────────────┬────────────────┘
        │               │                  │
        ▼               ▼                  ▼
   ┌─────────┐    ┌────────────┐    ┌──────────────┐
   │ Planning │    │ Virtual FS │    │  Sub-agents  │
   │ (todos)  │    │ (read/write│    │ (delegated   │
   │          │    │  files)    │    │  contexts)   │
   └─────────┘    └────────────┘    └──────────────┘
        │               │                  │
        └───────────────┴──────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  Tools / MCP /   │
              │  External APIs   │
              └──────────────────┘
```

### Core Components

- **Orchestrator (main loop):** Receives the user goal, plans, calls tools, delegates, and
  synthesizes the final answer. Owns the overall context budget.
- **Planning tool (todos):** A scratchpad of tasks with status (pending / in-progress / done).
  Updated as the agent works so intent stays explicit and recoverable.
- **Virtual file system:** Key/value or path-based storage the agent reads from and writes to.
  Used for offloading large outputs, sharing state between sub-agents, and durable artifacts.
- **Sub-agents:** Spawned for bounded sub-tasks (research, review, transformation). They get a
  focused prompt and isolated context, then return a compact result. Prefer them when a task
  would otherwise flood the parent context.
- **Tools:** Anything the agent can call — file ops, search, code execution, MCP servers,
  external APIs.

## Context Engineering Principles

- **Offload to files, not context.** Large intermediate data lives in the virtual FS; the
  context window holds pointers and summaries.
- **Isolate via sub-agents.** Delegate work whose detail the parent doesn't need to retain.
- **Plan explicitly.** Maintain the to-do list; re-read it to re-orient after long detours.
- **Summarize aggressively.** When context grows, compress completed work into a short note.
- **One responsibility per sub-agent.** Narrow prompts yield reliable, composable results.

## Conventions for This Project

- Place reusable agent context (like this file) under `memory/`.
- Use `notes/` for working notes and to-do tracking.
- Keep secrets in `.env`; never hardcode keys in notebooks or agent prompts.
- When adding a new agent capability, document its tool contract and expected output here.

## References

- LangChain `deepagents` package — planning + virtual FS + sub-agents scaffolding.
- Anthropic guidance on building effective agents and context engineering.
