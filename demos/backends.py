"""
backends.py
===========

Where a deep agent's files live, and how long they survive. Each demo asks the agent
to write ``/notes/todo.txt`` and then read it back under a progressively harder
condition:

* ``state``      -> ``StateBackend``: files live in the conversation state. They persist
                    *within* a thread only if you carry the state forward yourself.
* ``filesystem`` -> ``FilesystemBackend``: files map onto real disk (here
                    ``demos/notes/todo.txt``), so a brand-new agent can read them.
* ``store``      -> ``StoreBackend``: files live in a LangGraph ``BaseStore``, so a
                    *different thread* of the same agent can read them.

Run with:  ``uv run python demos/backends.py [demo ...]``
(no demo names = run them all). Needs ``GROQ_API_KEY``.
"""

from __future__ import annotations

import argparse
import uuid
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, StateBackend, StoreBackend
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.store.memory import InMemoryStore

# ---------------------------------------------------------------------------
# Paths & environment
# ---------------------------------------------------------------------------
# This file lives in  <repo>/demos/backends.py
DEMO_DIR = Path(__file__).resolve().parent
load_dotenv(DEMO_DIR.parent / ".env")  # repo-root .env

MODEL = "openai/gpt-oss-20b"

WRITE_PROMPT = (
    "Create a file at /notes/todo.txt with exactly this content:\n"
    "1. Record video\n2. Edit video\n3. Upload video\n"
    "Then tell me you've done it."
)
READ_PROMPT = "Read /notes/todo.txt back to me verbatim."


def ask(content: str) -> dict:
    return {"messages": [{"role": "user", "content": content}]}


# ---------------------------------------------------------------------------
# Demos
# ---------------------------------------------------------------------------
def demo_state() -> None:
    """StateBackend: files exist only in the state you pass back in."""
    agent = create_deep_agent(ChatGroq(model=MODEL), backend=StateBackend())

    result = agent.invoke(ask(WRITE_PROMPT))
    print(result["messages"][-1].content)

    print("\n--- Backend check -----------------------------------------------")
    files = result.get("files", {})
    if files:
        print(f"StateBackend is working — {len(files)} file(s) in state:")
        for path, data in files.items():
            print(f"\n{path}\n{'-' * 40}\n{data['content']}")
    else:
        print("No files found in state. Either the agent didn't write a file, "
              "or the backend isn't wired up correctly.")

    # Prove persistence WITHIN the same thread: feed the returned state back in.
    followup = agent.invoke({
        "messages": result["messages"] + ask(READ_PROMPT)["messages"],
        "files": result.get("files", {}),  # <-- pass the virtual filesystem along
    })
    print("\n--- Read-back (same thread) -------------------------------------")
    print(followup["messages"][-1].content)


def demo_filesystem() -> None:
    """FilesystemBackend: files land on real disk and survive the agent."""
    # virtual_mode=True -> the agent uses virtual paths like /notes/todo.txt,
    # mapped onto root_dir, and cannot escape it.
    agent = create_deep_agent(
        ChatGroq(model=MODEL),
        backend=FilesystemBackend(root_dir=str(DEMO_DIR), virtual_mode=True),
    )
    print(f"Agent created with FilesystemBackend(root_dir={str(DEMO_DIR)!r}).")
    print("Files written by the agent will appear on your ACTUAL disk.")

    result = agent.invoke(ask(WRITE_PROMPT))
    print(result["messages"][-1].content)

    print("\n--- Backend check (real filesystem) -----------------------------")
    disk_path = DEMO_DIR / "notes" / "todo.txt"
    if disk_path.exists():
        print("FilesystemBackend is working — file exists on disk:")
        print(f"{disk_path}\n{'-' * 40}")
        print(disk_path.read_text(encoding="utf-8"))
    else:
        print(f"Expected file not found at {disk_path}")
        print("The agent may not have called the write tool, or the path mapping differs.")

    # Prove persistence ACROSS sessions: a brand-new agent with fresh state
    # reads the file straight from disk (no `files` state passed in).
    fresh_agent = create_deep_agent(
        ChatGroq(model=MODEL),
        backend=FilesystemBackend(root_dir=str(DEMO_DIR), virtual_mode=True),
    )
    followup = fresh_agent.invoke(ask(READ_PROMPT))
    print("\n--- Read-back with a FRESH agent (proves disk persistence) ------")
    print(followup["messages"][-1].content)


def demo_store() -> None:
    """StoreBackend: files are shared across threads of the same agent."""
    store = InMemoryStore()
    agent = create_deep_agent(
        ChatGroq(model=MODEL),
        backend=StoreBackend(
            # Local dev: static namespace. No deployment runtime needed.
            # In a LangSmith Deployment you'd use the user-identity version.
            namespace=lambda rt: ("demo-user",),
        ),
        store=store,
    )
    print("Agent created with StoreBackend + static namespace.")

    thread_1 = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = agent.invoke(ask(WRITE_PROMPT), config=thread_1)
    print("\n--- Agent reply (thread 1) --------------------------------------")
    print(result["messages"][-1].content)

    thread_2 = {"configurable": {"thread_id": str(uuid.uuid4())}}
    followup = agent.invoke(ask(READ_PROMPT), config=thread_2)
    print("\n--- Read-back on a different thread -----------------------------")
    print(followup["messages"][-1].content)


DEMOS = {"state": demo_state, "filesystem": demo_filesystem, "store": demo_store}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare deep-agent file backends.")
    parser.add_argument("demos", nargs="*", choices=DEMOS, help="demos to run (default: all)")
    for name in parser.parse_args().demos or DEMOS:
        print(f"\n===== {name} =====")
        DEMOS[name]()


if __name__ == "__main__":
    main()
