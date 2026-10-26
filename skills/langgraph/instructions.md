# LangGraph — Detailed Instructions

Detailed guidance for designing LangGraph agents. Pairs with `instruction.md`
(checklist) and `examples.md` (code).

## 1. State design

- The state is the single source of truth that flows through every node. Model it with a
  `TypedDict` and annotate keys whose updates need merging with a **reducer**.
- The canonical example is messages: `Annotated[list[AnyMessage], add_messages]` so each
  node *appends* rather than *replaces* the conversation.
- Keep the state lean. Offload large intermediate artifacts to files (the virtual FS in
  `deepagents`) and keep only references/summaries in state — this is core context
  engineering for long-horizon runs.

## 2. Nodes

- A node is `def node(state: State) -> dict`. It returns a **partial** update, not the
  whole state. LangGraph merges it (respecting reducers).
- Keep nodes single-responsibility: an LLM-call node, a tool node, a router, etc.
- Side effects (API calls, file writes) belong in nodes; pure routing logic belongs in
  conditional-edge functions.

## 3. Edges & control flow

- `graph.add_edge(START, "agent")` sets the entry; `add_edge("x", END)` terminates.
- **Conditional edges** drive branching and loops:
  `graph.add_conditional_edges("agent", route_fn, {"tools": "tools", "end": END})`.
  `route_fn(state)` returns a key that maps to the next node.
- Build the **ReAct loop** as: agent → (conditional) → tools → agent → … → END.
- Guard against runaway loops with `recursion_limit` in the run config.

## 4. Tools

- Define tools with the `@tool` decorator or as functions with clear docstrings/schemas.
- Bind them so the model can emit tool calls: `model.bind_tools(tools)`.
- Use the prebuilt `ToolNode(tools)` to execute calls and append `ToolMessage`s.
- The prebuilt `tools_condition` helper handles "are there tool calls?" routing.

## 5. Persistence & memory

- Compile with a checkpointer to persist state between turns and enable resume:
  `graph.compile(checkpointer=MemorySaver())` (use sqlite/postgres savers in production).
- Each conversation/thread is identified by `config={"configurable": {"thread_id": id}}`.
- Checkpointing also enables **time-travel** (replay/fork from a past state) and
  **human-in-the-loop** (interrupt, inspect, edit, resume).

## 6. Human-in-the-loop

- Use `interrupt_before=["sensitive_node"]` at compile time, or call `interrupt(payload)`
  inside a node to pause. The run halts and surfaces the payload.
- Resume by invoking again with the same `thread_id` (and a `Command(resume=...)` if you
  used `interrupt()`).

## 7. Streaming

- `graph.stream(inputs, config, stream_mode="values" | "updates" | "messages")`.
  - `values`: full state after each step. `updates`: per-node deltas.
  - `messages`: token-level streaming of LLM output.
- Use `astream`/`astream_events` for async apps and fine-grained event hooks.

## 8. Prebuilt agents

- `from langgraph.prebuilt import create_react_agent` gives a ready tool-calling agent:
  `create_react_agent(model, tools, checkpointer=...)`.
- Start here for standard agents; drop to a hand-built `StateGraph` when you need custom
  routing, multiple cooperating nodes, or non-ReAct control flow.

## 9. deepagents (this project)

- `create_deep_agent(tools, instructions, subagents=[...])` wires planning (a todo tool),
  a **virtual file system** (read/write/ls/edit tools), **sub-agents**, and a strong
  system prompt on top of LangGraph.
- Define sub-agents with `{name, description, prompt, tools}`; the orchestrator delegates
  bounded sub-tasks to them so their detail never floods the parent context.
- Choose a backend (in-memory FS, or a persistent store) per the `backends.py` demo in
  `demos/`.

## 10. Pitfalls

- Forgetting a reducer → state keys silently overwrite each other.
- No `recursion_limit` → infinite agent↔tools loops on degenerate inputs.
- Putting huge payloads in state → context bloat; write to files instead.
- Reusing a `thread_id` unintentionally → mixing two conversations' memory.
