"""
subagents.py
============

Delegating bounded work to sub-agents, each with its own clean context.

* ``research``   -> the orchestrator hands an in-depth research question to a
                    ``research-agent`` sub-agent (via the built-in ``task`` tool).
* ``structured`` -> the sub-agent returns :class:`ResearchFindings` (summary /
                    confidence / sources) through ``response_format`` instead of
                    free text.

Each demo prints the full conversation, so the ``task`` tool call and the
sub-agent's reply are visible.

Run with:  ``uv run python demos/subagents.py [demo ...]``
(no demo names = run them all). Needs ``GROQ_API_KEY`` and ``TAVILY_API_KEY``.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Literal

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from tavily import TavilyClient

# ---------------------------------------------------------------------------
# Paths & environment
# ---------------------------------------------------------------------------
# This file lives in  <repo>/demos/subagents.py
REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

MODEL = "openai/gpt-oss-20b"


# ---------------------------------------------------------------------------
# Tools & schemas
# ---------------------------------------------------------------------------
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
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


class ResearchFindings(BaseModel):
    """Structured findings from a research task."""

    summary: str = Field(description="Summary of findings")
    confidence: float = Field(description="Confidence score from 0 to 1")
    sources: list[str] = Field(description="List of source URLs")


def print_conversation(result: dict[str, Any]) -> None:
    for m in result["messages"]:
        m.pretty_print()


# ---------------------------------------------------------------------------
# Demos
# ---------------------------------------------------------------------------
def demo_research() -> None:
    """Delegate an in-depth question to a research sub-agent."""
    research_subagent = {
        "name": "research-agent",
        "description": "Used to research more in depth questions",
        "system_prompt": "You are a great researcher",
        "tools": [internet_search],
        # Optional "provider:model" override; omit it to inherit the main agent's model.
        "model": f"groq:{MODEL}",
    }
    agent = create_deep_agent(model=ChatGroq(model=MODEL), subagents=[research_subagent])

    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Research LLM Gateways and provide me a detailed summary."}]}
    )
    print_conversation(result)


def demo_structured() -> None:
    """A sub-agent that returns typed findings via ``response_format``."""
    research_subagent = {
        "name": "researcher",
        "description": "Researches topics and returns structured findings",
        "system_prompt": "Research the given topic thoroughly. Return your findings.",
        "tools": [internet_search],
        "response_format": ResearchFindings,
    }
    agent = create_deep_agent(model=ChatGroq(model=MODEL), subagents=[research_subagent])

    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Research recent advances in quantum computing"}]}
    )
    print_conversation(result)


DEMOS = {"research": demo_research, "structured": demo_structured}


def main() -> None:
    parser = argparse.ArgumentParser(description="Delegate work to deep-agent sub-agents.")
    parser.add_argument("demos", nargs="*", choices=DEMOS, help="demos to run (default: all)")
    for name in parser.parse_args().demos or DEMOS:
        print(f"\n===== {name} =====")
        DEMOS[name]()


if __name__ == "__main__":
    main()
