"""
basicdeepagent.py
=================

A first deep agent: the same model and web-search tool wired up two ways.

* ``compare``  -> a plain LangChain tool-calling agent (``create_agent``) next to a
                  ``create_deep_agent`` one, printing the graph nodes each is built from.
                  The deep agent's extra nodes are the planning / file-system /
                  sub-agent middleware it gets for free. No model calls.
* ``research`` -> ask the deep agent a question and print its answer plus any files
                  it wrote to its virtual file system.

Run with:  ``uv run python demos/basicdeepagent.py [demo ...]``
(no demo names = run them all). Needs ``GROQ_API_KEY`` and ``TAVILY_API_KEY``.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Literal

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from tavily import TavilyClient

# ---------------------------------------------------------------------------
# Paths & environment
# ---------------------------------------------------------------------------
# This file lives in  <repo>/demos/basicdeepagent.py
REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

# gpt-oss-20b has reliable native tool calling and fits within Groq's free-tier
# tokens-per-minute limit, which gpt-oss-120b can exceed with the deep agent's
# large system prompt.
MODEL = "openai/gpt-oss-20b"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
def web_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "sports", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> Any:
    """Run a web search."""
    client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY", ""))
    return client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


def build_deep_agent():
    return create_deep_agent(
        model=ChatGroq(model=MODEL),
        tools=[web_search],
        system_prompt="Act as a researcher",
    )


# ---------------------------------------------------------------------------
# Demos
# ---------------------------------------------------------------------------
def demo_compare() -> None:
    """Plain tool-calling agent vs deep agent: same model, same tool."""
    plain_agent = create_agent(model=ChatGroq(model=MODEL), tools=[web_search])
    deep_agent = build_deep_agent()

    print("Plain agent nodes:", list(plain_agent.get_graph().nodes))
    print("Deep agent nodes: ", list(deep_agent.get_graph().nodes))


def demo_research() -> None:
    """Invoke the deep agent and inspect its answer and virtual file system."""
    result = build_deep_agent().invoke(
        {"messages": [{"role": "user", "content": "What is deepagent?"}]}
    )

    print(result["messages"][-1].content)
    print("\n--- Files in the virtual file system ---")
    print(result.get("files") or "(none)")


DEMOS = {"compare": demo_compare, "research": demo_research}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and run a first deep agent.")
    parser.add_argument("demos", nargs="*", choices=DEMOS, help="demos to run (default: all)")
    for name in parser.parse_args().demos or DEMOS:
        print(f"\n===== {name} =====")
        DEMOS[name]()


if __name__ == "__main__":
    main()
