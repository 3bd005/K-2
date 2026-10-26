"""
K-2 — Streamlit UI
==================

A conversational chatbot that exercises every capability built across the
``demos/`` scripts and the project's skills:

* Web search (Tavily) tool calling
* Swappable virtual-filesystem backends (State / Filesystem / Store)
* Delegated research sub-agents (incl. structured-output sub-agent)
* Dynamically loaded skills (langgraph / python / aws)
* Persistent project memory (AGENTS.md)
* Cross-turn conversation memory via a checkpointer + thread_id
* Optional QuickJS code-interpreter middleware
* Live view of the agent's plan (todos), tool calls, sub-agent calls and files

Run with:  ``uv run streamlit run app/streamlit_app.py``
"""

from __future__ import annotations

import uuid
from typing import Any

import streamlit as st

from agent_core import (
    AVAILABLE_MODELS,
    GROQ_MODELS,
    AgentConfig,
    build_agent,
    discover_skills,
    extract_files,
    extract_todos,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="K-2",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Session state bootstrap
# ---------------------------------------------------------------------------
def _init_state() -> None:
    ss = st.session_state
    ss.setdefault("thread_id", str(uuid.uuid4()))
    ss.setdefault("history", [])          # list[dict] for rendering the chat
    ss.setdefault("built", None)          # BuiltAgent
    ss.setdefault("built_signature", None)
    ss.setdefault("seeded", False)        # have skills/memory been seeded this thread?
    ss.setdefault("last_files", {})       # latest virtual FS snapshot
    ss.setdefault("last_todos", [])       # latest plan snapshot


_init_state()


# ---------------------------------------------------------------------------
# Sidebar — agent configuration
# ---------------------------------------------------------------------------
def render_sidebar() -> AgentConfig:
    st.sidebar.title("🧠 K-2")
    st.sidebar.caption("Configure the agent, then chat. Changing a setting rebuilds the agent.")

    with st.sidebar.expander("🤖 Model", expanded=True):
        model = st.selectbox("Model", AVAILABLE_MODELS, index=0)

    with st.sidebar.expander("💾 Backend (virtual file system)", expanded=True):
        backend_label = st.radio(
            "Where do the agent's files live?",
            ["State (per-thread, ephemeral)", "Filesystem (real disk)", "Store (durable, cross-thread)"],
            index=0,
            help="State = backends.py StateBackend; Filesystem = real disk; "
            "Store = cross-thread persistent store.",
        )
        backend = {"State": "state", "Filesystem": "filesystem", "Store": "store"}[
            backend_label.split(" ")[0]
        ]

    with st.sidebar.expander("🛠️ Capabilities", expanded=True):
        enable_web = st.toggle("Web search (Tavily)", value=True)
        enable_subagents = st.toggle("Research sub-agents", value=True)
        enable_structured = st.toggle(
            "Add structured-output sub-agent",
            value=False,
            disabled=not enable_subagents,
            help="A sub-agent that returns summary / confidence / sources via response_format.",
        )
        enable_memory = st.toggle("Project memory (AGENTS.md)", value=True)
        enable_code = st.toggle(
            "Code interpreter (QuickJS)",
            value=False,
            help="Adds langchain_quickjs CodeInterpreterMiddleware so the agent can run code.",
        )

    with st.sidebar.expander("📚 Skills", expanded=True):
        all_skills = discover_skills()
        enable_skills = st.toggle("Enable skills", value=bool(all_skills))
        on_disk = backend == "filesystem"
        selected_skills = st.multiselect(
            "Skills to load",
            all_skills,
            default=all_skills,
            disabled=not enable_skills or on_disk,
            help="The Filesystem backend reads every skill in ./skills/ from disk."
            if on_disk
            else "Each skill's files are seeded into /skills/ for on-demand use.",
        )

    with st.sidebar.expander("📝 System prompt", expanded=False):
        default_cfg = AgentConfig()
        system_prompt = st.text_area(
            "Orchestrator system prompt",
            value=default_cfg.system_prompt,
            height=160,
        )

    cfg = AgentConfig(
        model=model,
        backend=backend,  # type: ignore[arg-type]
        system_prompt=system_prompt,
        enable_web_search=enable_web,
        enable_subagents=enable_subagents,
        enable_structured_subagent=enable_structured,
        enable_skills=enable_skills,
        enable_memory=enable_memory,
        enable_code_interpreter=enable_code,
        selected_skills=selected_skills,
    )

    st.sidebar.divider()
    col_a, col_b = st.sidebar.columns(2)
    if col_a.button("🧹 New chat", width="stretch"):
        st.session_state.history = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.seeded = False
        st.session_state.last_files = {}
        st.session_state.last_todos = []
        st.session_state["_prev_msg_count"] = 0
        st.rerun()
    if col_b.button("🔄 Rebuild", width="stretch", help="Force-rebuild the agent"):
        st.session_state.built = None  # ensure_agent() rebuilds on this run

    st.sidebar.caption(f"Thread: `{st.session_state.thread_id[:8]}…`")
    if model in GROQ_MODELS:
        st.sidebar.info(
            "Groq free tier caps requests at ~8000 tokens/min. If you hit a 413 "
            "error, load fewer skills, shorten the system prompt, or use a smaller "
            "model (`openai/gpt-oss-20b`).",
            icon="ℹ️",
        )
    return cfg


# ---------------------------------------------------------------------------
# Agent lifecycle — rebuild only when the config signature changes
# ---------------------------------------------------------------------------
def ensure_agent(cfg: AgentConfig):
    sig = cfg.signature()
    if st.session_state.built is None or st.session_state.built_signature != sig:
        with st.spinner("Building deep agent…"):
            try:
                st.session_state.built = build_agent(cfg)
            except Exception as exc:  # usually a missing API key for the chosen provider
                st.session_state.built = None
                st.error(
                    f"⚠️ **Couldn't build the agent:** `{type(exc).__name__}: {exc}`\n\n"
                    "Check that this model's provider key is set in the repo-root `.env`."
                )
                st.stop()
            st.session_state.built_signature = sig
            # A rebuilt agent has a fresh checkpointer/store → re-seed and
            # reset the per-thread message counter.
            st.session_state.seeded = False
            st.session_state["_prev_msg_count"] = 0
    return st.session_state.built


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------
def _msg_text(msg: Any) -> str:
    content = getattr(msg, "content", "")
    if isinstance(content, list):  # content blocks
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", "") or block.get("content", ""))
            else:
                parts.append(str(block))
        return "".join(parts)
    return content if isinstance(content, str) else str(content)


def render_run_details(new_messages: list[Any]) -> None:
    """Show tool calls / sub-agent calls produced during a single run."""
    tool_calls = []
    for m in new_messages:
        for tc in getattr(m, "tool_calls", None) or []:
            tool_calls.append(tc)
    if not tool_calls:
        return
    with st.expander(f"🔎 Agent activity — {len(tool_calls)} tool/sub-agent call(s)"):
        for tc in tool_calls:
            name = tc.get("name", "tool") if isinstance(tc, dict) else getattr(tc, "name", "tool")
            args = tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {})
            icon = "🧩" if name == "task" else "🛠️"
            st.markdown(f"{icon} **{name}**")
            st.json(args, expanded=False)


def render_history() -> None:
    for entry in st.session_state.history:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])
            if entry.get("new_messages"):
                render_run_details(entry["new_messages"])


def render_state_panels() -> None:
    """Right-hand panels: the agent's plan and its virtual file system."""
    todos = st.session_state.last_todos
    files = st.session_state.last_files

    st.subheader("🗂️ Agent state")

    st.markdown("**Plan / todos**")
    if todos:
        status_icon = {"completed": "✅", "in_progress": "🔄", "pending": "⏳"}
        for t in todos:
            icon = status_icon.get(str(t.get("status", "")).lower(), "•")
            st.markdown(f"{icon} {t.get('content', '')}")
    else:
        st.caption("No plan yet — ask for a multi-step task.")

    st.divider()
    st.markdown("**Virtual file system**")
    if files:
        for path, content in files.items():
            with st.expander(path):
                st.code(content)
    else:
        st.caption("No files written yet.")


# ---------------------------------------------------------------------------
# Main turn handler
# ---------------------------------------------------------------------------
def run_turn(built, prompt: str) -> None:
    agent = built.agent
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    invoke_input: dict[str, Any] = {"messages": [{"role": "user", "content": prompt}]}
    # Seed skills + memory files once per thread (StateBackend needs them in state).
    if not st.session_state.seeded and built.seed_files:
        invoke_input["files"] = built.seed_files
    st.session_state.seeded = True

    prev_count = st.session_state.get("_prev_msg_count", 0)

    with st.chat_message("assistant"):
        with st.spinner("Thinking… (planning, tools, sub-agents)"):
            try:
                result = agent.invoke(invoke_input, config=config)
            except Exception as exc:  # surface errors instead of crashing the app
                err = f"⚠️ **Error during agent run:** `{type(exc).__name__}: {exc}`"
                st.markdown(err)
                st.session_state.history.append(
                    {"role": "assistant", "content": err, "new_messages": []}
                )
                return

        messages = result.get("messages", [])
        new_messages = messages[prev_count:] if prev_count else messages
        st.session_state["_prev_msg_count"] = len(messages)

        # final assistant text = last message content
        answer = _msg_text(messages[-1]) if messages else "(no response)"
        st.markdown(answer)
        render_run_details(new_messages)

        # snapshot plan + files for the state panels
        st.session_state.last_files = extract_files(result)
        st.session_state.last_todos = extract_todos(result)

    st.session_state.history.append(
        {"role": "assistant", "content": answer, "new_messages": new_messages}
    )


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------
def main() -> None:
    cfg = render_sidebar()
    built = ensure_agent(cfg)

    st.title("🧠 K-2")
    st.caption(
        "An integrated deep agent: planning · virtual file system · sub-agents · "
        "skills · persistent memory · web search."
    )

    chat_col, state_col = st.columns([3, 1.4], gap="large")

    with state_col:
        render_state_panels()

    with chat_col:
        render_history()

        if prompt := st.chat_input("Ask K-2 anything…"):
            st.session_state.history.append(
                {"role": "user", "content": prompt, "new_messages": []}
            )
            with st.chat_message("user"):
                st.markdown(prompt)
            run_turn(built, prompt)
            # refresh the state panels after the turn
            st.rerun()


if __name__ == "__main__":
    main()
