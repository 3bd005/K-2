# LangGraph — Quick Instruction Checklist

Scannable checklist for building a LangGraph agent. For depth, see `instructions.md`.

## Design the state first
- [ ] Define a `TypedDict` (or `pydantic` model) for the graph state.
- [ ] For message history, use `Annotated[list, add_messages]` as the reducer.
- [ ] Keep large blobs out of state — store pointers / write to the virtual FS.

## Build the graph
- [ ] Create `StateGraph(StateSchema)`.
- [ ] Add nodes as pure-ish functions returning **partial** state updates.
- [ ] Add an entry edge from `START`; add `END` for terminal paths.
- [ ] Use **conditional edges** for branching and the tool-calling loop.
- [ ] Compile with a **checkpointer** if you need memory/resume.

## Tool calling loop
- [ ] Bind tools to the model: `model.bind_tools(tools)`.
- [ ] Add a `ToolNode(tools)`.
- [ ] Conditional edge: if last AI message has tool calls → tools node, else → END.
- [ ] Edge from tools node back to the model node (the loop).

## Run it
- [ ] Pass `config={"configurable": {"thread_id": "..."}}` when using a checkpointer.
- [ ] Use `graph.stream(...)` for incremental output; `invoke` for one-shot.

## deepagents shortcut
- [ ] For long-horizon tasks, prefer `create_deep_agent(tools, instructions, subagents=...)`
      instead of hand-wiring planning + FS + sub-agents.

## Before declaring done
- [ ] No unhandled tool errors; tool outputs validated.
- [ ] Recursion/step limit set to avoid infinite loops (`recursion_limit`).
- [ ] Secrets (API keys) read from env, not hardcoded.
