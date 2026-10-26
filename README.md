# 🧠 K-2

**K-2** is a **deep agent** — a long-horizon, multi-step LLM assistant — built on
[`deepagents`](https://github.com/langchain-ai/deepagents), LangChain and LangGraph,
wrapped in a Streamlit chat UI.

Unlike a plain tool-calling loop, this agent combines four capabilities that let it stay
coherent across many steps:

1. **Explicit planning** — it writes and maintains a to-do list as it works.
2. **A virtual file system** — large intermediate results are offloaded to files instead of
   bloating the context window.
3. **Sub-agents** — bounded sub-tasks (research, structured extraction) are delegated to
   child agents with their own clean context.
4. **A detailed system prompt + skills** — reference knowledge is loaded on demand rather
   than crammed into every request.

The repo contains both the **runnable app** (`app/`) and the **teaching demo scripts**
(`demos/`) that each capability was developed in.

---

## Quick start

```bash
# 1. Install dependencies (uv reads pyproject.toml + uv.lock)
uv sync

# 2. Add your API keys
cp .env.example .env
#    then edit .env

# 3. Run the chatbot
uv run streamlit run app/streamlit_app.py
```

Streamlit opens on <http://localhost:8501>.

> Requires **Python 3.14** (pinned in `.python-version`). Prefer pip? `pip install -r req.txt`.

### API keys

| Variable | Needed for | Where to get it |
|---|---|---|
| `GOOGLE_API_KEY` | Gemini models — **the default**, free tier + reliable tool calling | [aistudio.google.com](https://aistudio.google.com/apikey) |
| `TAVILY_API_KEY` | The `internet_search` tool | [tavily.com](https://tavily.com) |
| `GROQ_API_KEY` | Groq-served open-weight models (gpt-oss) and the demo scripts | [console.groq.com](https://console.groq.com/keys) |
| `OPENAI_API_KEY` | `gpt-6-luna` / `gpt-6.1-sol` (requires billing) | [platform.openai.com](https://platform.openai.com/api-keys) |

The app and the demo scripts both read keys from the repo-root `.env`, which is git-ignored —
only `.env.example` is committed.

---

## Using the app

The sidebar reconfigures the agent live; changing any setting rebuilds it and starts a fresh
memory thread.

| Control | What it does |
|---|---|
| **Model** | Gemini → Groq → OpenAI. Gemini is first because it is free *and* reliable at tool calling. |
| **Backend** | `State` (per-thread, ephemeral) · `Filesystem` (real disk under the repo) · `Store` (durable, cross-thread) |
| **Web search** | Adds the Tavily `internet_search` tool to the agent and its sub-agents |
| **Research sub-agents** | Enables the delegated `research-agent` |
| **Structured-output sub-agent** | Adds `structured-researcher`, which returns `summary` / `confidence` / `sources` via `response_format` |
| **Project memory** | Loads `memory/AGENTS.md` as persistent agent memory |
| **Code interpreter** | Adds the QuickJS `CodeInterpreterMiddleware` so the agent can execute code |
| **Skills** | Multiselect over `skills/*/SKILL.md`, seeded under the virtual `/skills/` path (the Filesystem backend always reads every skill from disk) |
| **System prompt** | Editable orchestrator prompt |

The right-hand **Agent state** panel shows the live plan (todos) and the contents of the
virtual file system. Each answer carries an expandable **Agent activity** log listing every
tool and sub-agent call made during that turn.

---

## Project layout

```
.
├── app/                       # the Streamlit chatbot
│   ├── agent_core.py          #   build_agent() factory — models, tools, backends,
│   │                          #   sub-agents, skills, memory, middleware
│   ├── streamlit_app.py       #   chat UI, conversation threading, state panels
│   └── README.md              #   app-level notes
│
├── demos/                     # the demo scripts each capability came from
│   ├── basicdeepagent.py      #   create_deep_agent + Tavily search + prompts
│   ├── backends.py            #   State vs Filesystem vs Store backends
│   ├── subagents.py           #   delegation + structured output
│   └── contextEng.py          #   system prompt, memory, checkpointing, skills
│
├── memory/
│   └── AGENTS.md              # architecture + context-engineering doc, loaded as memory
│
├── skills/                    # on-demand reference knowledge
│   ├── python/                #   each: SKILL.md (entry) + instruction.md (checklist)
│   ├── langgraph/             #         + instructions.md (depth) + examples.md (code)
│   └── aws/
│
├── .devcontainer/             # Codespaces / dev container config (port 8501)
├── .env.example               # API-key template — copy to .env
└── pyproject.toml · uv.lock · req.txt · .python-version
```

---

## How it fits together

```
┌──────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                    │
│      system prompt · planning loop · context mgmt        │
└───────┬──────────────┬──────────────┬────────────────────┘
        ▼              ▼              ▼
   ┌─────────┐   ┌────────────┐  ┌──────────────┐
   │ Planning│   │ Virtual FS │  │  Sub-agents  │
   │ (todos) │   │ (backend)  │  │  (isolated   │
   │         │   │            │  │   contexts)  │
   └─────────┘   └────────────┘  └──────────────┘
        └──────────────┴──────────────┘
                       ▼
            ┌──────────────────────┐
            │ Tools: Tavily search │
            │ QuickJS interpreter  │
            └──────────────────────┘
```

**Backends** decide where the agent's files live:

- `StateBackend` — files live in the conversation state. Fast, ephemeral, per-thread.
- `FilesystemBackend` — files map to real paths under the repo root (`virtual_mode=True`
  confines the agent there). Survives restarts. `skills/` and `memory/AGENTS.md` are read in
  place from disk rather than seeded.
- `StoreBackend` — files live in a LangGraph `BaseStore`, shared across threads. Swap
  `InMemoryStore` for Postgres to make it genuinely durable.

**Memory** works on two levels: a `MemorySaver` checkpointer keyed by `thread_id` carries the
conversation across turns, while `AGENTS.md` is loaded as long-term project context on every
invocation.

**Skills** are folders under `skills/`. Each skill's files are seeded into the virtual FS,
but only the `SKILL.md` frontmatter goes into the prompt; the agent reads `instruction.md`,
`instructions.md`, or `examples.md` on demand when a query actually needs that depth. To add
one, create `skills/<name>/SKILL.md` with YAML frontmatter (`name` matching the folder name,
`description`, `metadata`) — `discover_skills()` picks it up automatically, no code change
required. The entry file must be named exactly `SKILL.md`: deepagents ignores any other
casing.

---

## Demo scripts

Each script in `demos/` is a set of named demos, listed here in learning order. Run all of
them, or name the ones you want — each demo makes real model calls, so picking a few keeps
you under Groq's free-tier rate limit:

```bash
uv run python demos/backends.py              # every demo
uv run python demos/backends.py state store  # just these
uv run python demos/backends.py --help       # list demos
```

| Script | Demos | Covers |
|---|---|---|
| `basicdeepagent.py` | `compare` `research` | A plain tool-calling agent vs `create_deep_agent`, the Tavily search tool, prompt design |
| `backends.py` | `state` `filesystem` `store` | Proving persistence within a thread, across sessions, and across threads |
| `subagents.py` | `research` `structured` | Delegating research to an isolated context; structured output via `response_format` |
| `contextEng.py` | `prompt` `inline-memory` `state-memory` `store-memory` `fs-memory` `skills` | System prompts, `AGENTS.md` memory on each backend, checkpointing, dynamically loaded skills |

The scripts use Groq's `openai/gpt-oss-20b` and need `GROQ_API_KEY` (plus `TAVILY_API_KEY`
for the ones that search). `backends.py filesystem` doubles as a quick smoke test: it has
the agent write `demos/notes/todo.txt` to real disk, then reads it back with a fresh agent.

---

## Troubleshooting

**`404` / model not found** — the provider has retired that model. The lineup lives in the
`GEMINI_MODELS` / `GROQ_MODELS` / `OPENAI_MODELS` lists at the top of
`app/agent_core.py`; swap in a current model ID from the provider's models page.

**Slow replies on Gemini** — Gemini 3 models reason before every step, and a deep agent takes
many steps per turn. The app sets `thinking_level="low"`; raise it in `build_agent()` for harder
tasks.

**`tool_use_failed` (400) on Groq models** — the open-weight models intermittently emit
malformed `<function=...>` tool-call syntax that Groq rejects. Switch to a Gemini model, or retry.

**`413 Request too large` on Groq** — the free tier caps requests at roughly 8000 tokens/min.
Load fewer skills, shorten the system prompt, or drop to `openai/gpt-oss-20b`. The UI catches
these errors and shows them inline instead of crashing.

**Missing key errors** — `internet_search` imports Tavily lazily, so the app starts fine
without `TAVILY_API_KEY`; it only fails when the tool is actually called.

---

## Dev container

`.devcontainer/devcontainer.json` builds a Python image, forwards port **8501**, and
auto-launches Streamlit on attach — usable directly in GitHub Codespaces.

---

## Tech stack

`deepagents` · `langchain` · `langgraph` · `langchain-google-genai` · `langchain-groq` ·
`langchain-openai` · `langchain-quickjs` · `tavily-python` · `streamlit` · `python-dotenv` · `uv`
