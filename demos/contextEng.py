"""
contextEng.py
=============

Context engineering: what a deep agent knows before it starts, and how that
context reaches it.

* ``prompt``        -> a custom ``system_prompt`` on top of the deep-agent defaults.
* ``inline-memory`` -> the naive approach: paste ``AGENTS.md`` into the user message.
* ``state-memory``  -> ``memory=[...]`` with ``AGENTS.md`` seeded into the in-state file system.
* ``store-memory``  -> the same memory held in a ``BaseStore``: durable, cross-thread.
* ``fs-memory``     -> the same memory read straight from disk via ``FilesystemBackend``.
* ``skills``        -> ``skills/*/`` seeded under ``/skills/``; the agent reads a skill's
                       files on demand, only when a question needs it.

Memory is loaded once per thread, which is why the demos use a ``MemorySaver``
checkpointer and an explicit ``thread_id``.

Run with:  ``uv run python demos/contextEng.py [demo ...]``
(no demo names = run them all). Needs ``GROQ_API_KEY``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

# ---------------------------------------------------------------------------
# Paths & environment
# ---------------------------------------------------------------------------
# This file lives in  <repo>/demos/contextEng.py
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS_MD = REPO_ROOT / "memory" / "AGENTS.md"
load_dotenv(REPO_ROOT / ".env")

MODEL = "openai/gpt-oss-20b"
MEMORY_QUESTION = "What's in your memory? Who are you?"


def ask(content: str) -> dict[str, Any]:
    return {"messages": [{"role": "user", "content": content}]}


def thread(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


# ---------------------------------------------------------------------------
# Demos — system prompt & memory
# ---------------------------------------------------------------------------
def demo_prompt() -> None:
    """A custom system prompt layered on the deep-agent defaults."""
    agent = create_deep_agent(
        ChatGroq(model=MODEL),
        system_prompt=(
            "You are a research assistant specializing in scientific literature. "
            "Always cite sources. Use subagents for parallel research on different topics."
        ),
    )
    result = agent.invoke(ask("What is deep learning?"))
    print(result["messages"][-1].content)


def demo_inline_memory() -> None:
    """Naive: paste the project guide into the message itself (costs tokens every turn)."""
    agent = create_deep_agent(ChatGroq(model=MODEL), checkpointer=MemorySaver())
    agents_md = AGENTS_MD.read_text(encoding="utf-8")
    result = agent.invoke(
        ask(f"Here is our project guide:\n\n{agents_md}\n\nNow, who are you and what should you follow?"),
        config=thread("inline-demo-1"),
    )
    print(result["messages"][-1].content)


def demo_state_memory() -> None:
    """``memory=`` reads AGENTS.md from the in-state file system, seeded per thread."""
    agent = create_deep_agent(
        ChatGroq(model=MODEL),
        memory=["/memory/AGENTS.md"],  # must be the absolute virtual path that is seeded
        checkpointer=MemorySaver(),
    )
    result = agent.invoke(
        {
            **ask(MEMORY_QUESTION),
            "files": {"/memory/AGENTS.md": create_file_data(AGENTS_MD.read_text(encoding="utf-8"))},
        },
        config=thread("state-demo-1"),  # fresh thread => memory loads
    )
    print(result["messages"][-1].content)


def demo_store_memory() -> None:
    """StoreBackend: memory lives in a BaseStore and survives threads and rebuilds."""
    # Swap InMemoryStore for a persistent store (e.g. Postgres) for real durability.
    store = InMemoryStore()
    # Seed durable memory into the store once. The key is the file's full virtual path.
    store.put(("memories",), "/memory/AGENTS.md", create_file_data(AGENTS_MD.read_text(encoding="utf-8")))

    agent = create_deep_agent(
        ChatGroq(model=MODEL),
        backend=StoreBackend(store=store, namespace=lambda rt: ("memories",)),
        memory=["/memory/AGENTS.md"],  # read from the store, not state or disk
        store=store,
        checkpointer=MemorySaver(),
    )
    # No files= seeding needed — the store already holds it.
    result = agent.invoke(ask(MEMORY_QUESTION), config=thread("store-demo-1"))
    print(result["messages"][-1].content)


def demo_fs_memory() -> None:
    """FilesystemBackend: nothing to seed — AGENTS.md is read straight from disk."""
    # root_dir = the memory/ folder, so the memory path is relative to it.
    # virtual_mode=True confines the agent to root_dir.
    agent = create_deep_agent(
        model=ChatGroq(model=MODEL),
        backend=FilesystemBackend(root_dir=str(AGENTS_MD.parent), virtual_mode=True),
        memory=["/AGENTS.md"],  # -> <repo>/memory/AGENTS.md
        checkpointer=MemorySaver(),
    )
    config = thread("fs-demo-1")
    result = agent.invoke(ask(MEMORY_QUESTION), config=config)
    print(result["messages"][-1].content)

    # Same thread: the memory loaded on the first turn still shapes the answer.
    result = agent.invoke(ask("What are LLM Gateways?"), config=config)
    print("\n--- Follow-up on the same thread ---")
    print(result["messages"][-1].content)


# ---------------------------------------------------------------------------
# Demos — skills
# ---------------------------------------------------------------------------
def load_skill_files() -> dict[str, Any]:
    """Seed every file of every ``skills/<name>/`` folder that ships a ``SKILL.md``.

    Only the ``SKILL.md`` frontmatter goes into the prompt; the companion files
    (``instruction.md``, ``examples.md``, ...) are there for the agent to read on demand.
    """
    files: dict[str, Any] = {}
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not (skill_dir / "SKILL.md").exists():
            continue
        for path in sorted(skill_dir.iterdir()):
            if path.is_file():
                files[f"/skills/{skill_dir.name}/{path.name}"] = create_file_data(
                    path.read_text(encoding="utf-8")
                )
    return files


def demo_skills() -> None:
    """Skills are listed up front but read only when a question needs one."""
    skills_files = load_skill_files()
    print("Seeded:", *skills_files, sep="\n  ")

    agent = create_deep_agent(
        model=ChatGroq(model=MODEL),
        backend=StateBackend(),
        skills=["/skills/"],
        checkpointer=MemorySaver(),
    )
    questions = [
        "What skills do you have available, and when would you use each?",
        "How do I build a LangGraph graph with conditional routing and memory? Show a minimal example.",
        "How do I set up an EC2 instance in AWS?",
        "Write me Python code to do a binary search.",
    ]
    for i, question in enumerate(questions, start=1):
        result = agent.invoke(
            {**ask(question), "files": skills_files},  # seed skills into THIS thread's state
            config=thread(f"skills-demo-{i}"),
        )
        # The skill "triggers" when the agent read_file's its SKILL.md / companions.
        reads = [
            tc["args"].get("file_path")
            for m in result["messages"]
            for tc in getattr(m, "tool_calls", None) or []
            if tc["name"] == "read_file"
        ]
        print(f"\n--- Q{i}: {question}")
        print("Files read:", reads or "(none)")
        print(result["messages"][-1].content)


DEMOS = {
    "prompt": demo_prompt,
    "inline-memory": demo_inline_memory,
    "state-memory": demo_state_memory,
    "store-memory": demo_store_memory,
    "fs-memory": demo_fs_memory,
    "skills": demo_skills,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Context engineering: prompts, memory and skills.")
    parser.add_argument("demos", nargs="*", choices=DEMOS, help="demos to run (default: all)")
    for name in parser.parse_args().demos or DEMOS:
        print(f"\n===== {name} =====")
        DEMOS[name]()


if __name__ == "__main__":
    main()
