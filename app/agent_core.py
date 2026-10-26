"""
agent_core.py
=============

The brain of the K-2 chatbot. This module wires together *every* deep-agent
capability demonstrated across the demo scripts in ``demos/`` and exposes a
single :func:`build_agent` factory plus a few helpers the UI layer consumes.

Capabilities integrated here (mapped to the demo scripts that introduce them):

* basicdeepagent.py     -> ``create_deep_agent`` + Tavily ``internet_search`` tool +
                           ChatGroq models + a researcher ``system_prompt``.
* backends.py           -> swappable ``StateBackend`` / ``FilesystemBackend`` /
                           ``StoreBackend`` virtual file systems.
* subagents.py          -> delegated ``research-agent`` sub-agent, including a
                           structured-output sub-agent (``response_format``).
* contextEng.py         -> persistent memory (``AGENTS.md``), ``MemorySaver``
                           checkpointing keyed by ``thread_id``, dynamically loaded
                           ``skills`` (langgraph / python / aws).

On top of those, the app adds an optional QuickJS code-interpreter middleware.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# --- deepagents / langchain / langgraph -------------------------------------
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

# ---------------------------------------------------------------------------
# Paths & environment
# ---------------------------------------------------------------------------
# This file lives in  <repo>/app/agent_core.py
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS_MD = REPO_ROOT / "memory" / "AGENTS.md"
# Virtual paths mirror the repo layout, so they are the same on every backend.
MEMORY_PATH = "/memory/AGENTS.md"

# API keys live in the repo-root .env, shared with the demo scripts.
load_dotenv(REPO_ROOT / ".env")


# ---------------------------------------------------------------------------
# Model catalogue
# ---------------------------------------------------------------------------
# Provider model lineups change often — check each provider's deprecations page
# when a model starts returning 404s. Last reviewed: 2026-10.

# Google Gemini models — free tier + reliable function calling (uses GOOGLE_API_KEY).
GEMINI_MODELS: list[str] = [
    "gemini-3.8-flash",            # default: free + reliable tool calling
    "gemini-3.5-flash-lite",       # faster / lighter
]

# Models served directly by OpenAI — reliable native tool calling (uses OPENAI_API_KEY).
OPENAI_MODELS: list[str] = [
    "gpt-6-luna",                  # cheap + reliable, but requires OpenAI account billing
    "gpt-6.1-sol",
]

# Models served by Groq's free tier — open-weight and fast, but they intermittently
# emit malformed <function=...> tool calls that Groq rejects (tool_use_failed), and
# carry tight per-minute token limits.
GROQ_MODELS: list[str] = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]

# Gemini first: free *and* reliable tool calling, so it's the default. Groq models
# are free but flaky at tool calls; OpenAI models need account billing.
AVAILABLE_MODELS: list[str] = GEMINI_MODELS + GROQ_MODELS + OPENAI_MODELS


# ---------------------------------------------------------------------------
# Tools  (basicdeepagent.py / subagents.py)
# ---------------------------------------------------------------------------
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> Any:
    """Run a web search via Tavily and return the raw results.

    Imported lazily so the app can still start (e.g. show config) when the
    Tavily key is missing; the tool only fails if actually invoked without a key.
    """
    from tavily import TavilyClient

    client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY", ""))
    return client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


# ---------------------------------------------------------------------------
# Structured output schema for the structured research sub-agent (subagents.py)
# ---------------------------------------------------------------------------
class ResearchFindings(BaseModel):
    """Structured findings returned by the structured research sub-agent."""

    summary: str = Field(description="Summary of findings")
    confidence: float = Field(description="Confidence score from 0 to 1")
    sources: list[str] = Field(description="List of source URLs")


# ---------------------------------------------------------------------------
# Skills loading  (contextEng.py)
# ---------------------------------------------------------------------------
def discover_skills() -> list[str]:
    """Return the names of every skill folder that ships a ``SKILL.md``."""
    if not SKILLS_DIR.exists():
        return []
    names = []
    for child in sorted(SKILLS_DIR.iterdir()):
        if child.is_dir() and (child / "SKILL.md").exists():
            names.append(child.name)
    return names


def load_skill_files(skill_names: list[str]) -> dict[str, Any]:
    """Read every file in each ``skills/<name>/`` folder and seed it into the virtual FS.

    Mirrors contextEng.py: skills are seeded under ``/skills/<name>/``
    and the agent is told skills live under ``/skills/``. deepagents only lists a
    skill whose entry file is named exactly ``SKILL.md``; the companion files
    (``instruction.md``, ``examples.md``, ...) are seeded alongside so the agent
    can read them on demand.
    """
    files: dict[str, Any] = {}
    for name in skill_names:
        skill_dir = SKILLS_DIR / name
        if not (skill_dir / "SKILL.md").exists():
            continue
        for path in sorted(skill_dir.iterdir()):
            if path.is_file():
                content = path.read_text(encoding="utf-8")
                files[f"/skills/{name}/{path.name}"] = create_file_data(content)
    return files


def load_memory_file() -> dict[str, Any]:
    """Seed the AGENTS.md project context as an in-state memory file."""
    if not AGENTS_MD.exists():
        return {}
    content = AGENTS_MD.read_text(encoding="utf-8")
    return {MEMORY_PATH: create_file_data(content)}


# ---------------------------------------------------------------------------
# Sub-agents  (subagents.py)
# ---------------------------------------------------------------------------
def build_subagents(enable_web: bool, structured: bool) -> list[dict[str, Any]]:
    """Construct the delegated research sub-agent(s).

    ``structured=True`` adds a second sub-agent that returns
    :class:`ResearchFindings` via ``response_format`` (structured output).
    """
    research_tools = [internet_search] if enable_web else []

    research_subagent: dict[str, Any] = {
        "name": "research-agent",
        "description": "Used to research more in-depth questions in an isolated context.",
        "system_prompt": "You are a great researcher. Investigate thoroughly and cite sources.",
        "tools": research_tools,
        # No "model" override: sub-agents inherit the orchestrator's model, so
        # they only need the API key of the provider picked in the sidebar.
    }

    subagents: list[dict[str, Any]] = [research_subagent]

    if structured:
        subagents.append(
            {
                "name": "structured-researcher",
                "description": "Researches a topic and returns structured findings "
                "(summary, confidence, sources).",
                "system_prompt": "Research the given topic thoroughly. Return your findings.",
                "tools": research_tools,
                "response_format": ResearchFindings,
            }
        )

    return subagents


# ---------------------------------------------------------------------------
# Backends  (backends.py)
# ---------------------------------------------------------------------------
BackendKind = Literal["state", "filesystem", "store"]


def build_backend(kind: BackendKind, store: InMemoryStore | None):
    """Return the requested backend instance.

    * ``state``      -> in-conversation virtual FS (per-thread, ephemeral).
    * ``filesystem`` -> real disk under the repo root (survives restarts).
    * ``store``      -> cross-thread persistent store (durable, shareable).
    """
    if kind == "state":
        return StateBackend()
    if kind == "filesystem":
        # virtual_mode confines the agent to the repo root and maps virtual
        # paths like /notes/todo.txt onto ./notes/todo.txt.
        return FilesystemBackend(root_dir=str(REPO_ROOT), virtual_mode=True)
    if kind == "store":
        return StoreBackend(store=store, namespace=lambda rt: ("k-2",))
    raise ValueError(f"Unknown backend kind: {kind!r}")


# ---------------------------------------------------------------------------
# Agent configuration & factory
# ---------------------------------------------------------------------------
@dataclass
class AgentConfig:
    """Everything the UI lets the user toggle. Hashable signature drives rebuilds."""

    model: str = GEMINI_MODELS[0]
    backend: BackendKind = "state"
    system_prompt: str = (
        "You are K-2, a Deep Agent: a long-horizon, multi-step assistant. "
        "Plan explicitly with the todo tool, offload large intermediate results to "
        "the virtual file system, delegate bounded research to sub-agents, and "
        "consult your skills before answering specialised questions. Always cite sources."
    )
    enable_web_search: bool = True
    enable_subagents: bool = True
    enable_structured_subagent: bool = False
    enable_skills: bool = True
    enable_memory: bool = True
    enable_code_interpreter: bool = False
    selected_skills: list[str] = field(default_factory=list)

    def signature(self) -> tuple:
        """A hashable tuple that changes whenever the agent must be rebuilt."""
        return (
            self.model,
            self.backend,
            self.system_prompt,
            self.enable_web_search,
            self.enable_subagents,
            self.enable_structured_subagent,
            self.enable_skills,
            self.enable_memory,
            self.enable_code_interpreter,
            tuple(self.selected_skills),
        )


@dataclass
class BuiltAgent:
    """An agent plus the shared store and the files that must be seeded once."""

    agent: Any
    store: InMemoryStore
    seed_files: dict[str, Any]


def build_agent(cfg: AgentConfig) -> BuiltAgent:
    """Create a fully-configured deep agent from a :class:`AgentConfig`."""
    # Route to the right provider by model id. Gemini and OpenAI use their own SDKs
    # (reliable native tool calling); everything else is served by Groq.
    if cfg.model in GEMINI_MODELS:
        from langchain_google_genai import ChatGoogleGenerativeAI

        # Gemini 3+ models reason before every reply (default level "high"). A deep
        # agent makes many model calls per turn, so keep reasoning light to keep
        # each step fast. No max_tokens cap: thinking tokens count against it, and
        # a tight cap can leave an empty reply with no tool call.
        model = ChatGoogleGenerativeAI(model=cfg.model, thinking_level="low")
    elif cfg.model in OPENAI_MODELS:
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(model=cfg.model)
    else:
        model = ChatGroq(model=cfg.model)

    # --- tools ---
    tools: list[Any] = []
    if cfg.enable_web_search:
        tools.append(internet_search)

    # --- optional QuickJS code-interpreter middleware ---
    middleware: list[Any] = []
    if cfg.enable_code_interpreter:
        from langchain_quickjs import CodeInterpreterMiddleware

        middleware.append(CodeInterpreterMiddleware())

    # --- shared store + checkpointer for cross-turn conversation memory ---
    store = InMemoryStore()
    checkpointer = MemorySaver()
    backend = build_backend(cfg.backend, store)

    kwargs: dict[str, Any] = {
        "model": model,
        "tools": tools,
        "system_prompt": cfg.system_prompt,
        "backend": backend,
        "checkpointer": checkpointer,
    }

    if cfg.enable_subagents:
        kwargs["subagents"] = build_subagents(
            enable_web=cfg.enable_web_search,
            structured=cfg.enable_structured_subagent,
        )

    if middleware:
        kwargs["middleware"] = middleware

    # --- seed files (skills + memory) into the virtual FS ---
    # The State and Store backends start empty, so skills and memory are seeded
    # into them. The Filesystem backend already sees the real repo, so it reads
    # the same paths in place (and therefore every skill under ./skills/).
    seed_files: dict[str, Any] = {}
    on_disk = cfg.backend == "filesystem"

    if cfg.enable_skills and cfg.selected_skills:
        kwargs["skills"] = ["/skills/"]
        if not on_disk:
            seed_files.update(load_skill_files(cfg.selected_skills))

    if cfg.enable_memory and AGENTS_MD.exists():
        kwargs["memory"] = [MEMORY_PATH]
        if not on_disk:
            seed_files.update(load_memory_file())

    # The StoreBackend needs the store handed to the agent too, and durable
    # memory must be put into the store rather than passed as state files.
    if cfg.backend == "store":
        kwargs["store"] = store
        for path, data in list(seed_files.items()):
            # Store keys are filenames within the namespace.
            store.put(("k-2",), path, data)
        # When using the store backend the files already live in the store, so
        # we don't need to re-seed them as per-turn state files.
        seed_files = {}

    agent = create_deep_agent(**kwargs)
    return BuiltAgent(agent=agent, store=store, seed_files=seed_files)


# ---------------------------------------------------------------------------
# Helpers for the UI to introspect a run's result
# ---------------------------------------------------------------------------
def extract_files(result: dict[str, Any]) -> dict[str, str]:
    """Return {path: text} for any files present in the run's state."""
    out: dict[str, str] = {}
    files = result.get("files") or {}
    for path, data in files.items():
        if isinstance(data, dict):
            content = data.get("content")
            if isinstance(content, list):  # line-oriented file data
                content = "".join(content)
            out[path] = content if isinstance(content, str) else str(data)
        else:
            out[path] = str(data)
    return out


def extract_todos(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the planning to-do list, if the agent maintained one."""
    todos = result.get("todos") or []
    norm: list[dict[str, Any]] = []
    for t in todos:
        if isinstance(t, dict):
            norm.append(t)
        else:  # pydantic / object
            norm.append(
                {
                    "content": getattr(t, "content", str(t)),
                    "status": getattr(t, "status", ""),
                }
            )
    return norm
