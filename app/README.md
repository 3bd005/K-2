# 🧠 K-2 — Streamlit app

A conversational chatbot that integrates **every** capability built across the
`demos/` scripts and the project's `skills/`.

## What it integrates

| Feature | Source demo script | In the app |
|---|---|---|
| `create_deep_agent` + Tavily web search + ChatGroq | `basicdeepagent.py` | "Web search" toggle, model selector |
| State / Filesystem / Store backends | `backends.py` | "Backend" radio in the sidebar |
| Delegated research sub-agents | `subagents.py` | "Research sub-agents" toggle |
| Structured-output sub-agent (`response_format`) | `subagents.py` | "Add structured-output sub-agent" toggle |
| Dynamically loaded skills (`langgraph`, `python`, `aws`) | `contextEng.py` | "Skills" multiselect |
| Project memory (`AGENTS.md`) | `contextEng.py` | "Project memory" toggle |
| Cross-turn memory (checkpointer + `thread_id`) | `contextEng.py` | automatic per chat session |
| QuickJS code-interpreter middleware | — (app only) | "Code interpreter" toggle |
| Planning (todos) + virtual file system | `AGENTS.md` architecture | live "Agent state" panel |

## Run it

```bash
# from the repo root
uv run streamlit run app/streamlit_app.py
```

Then open the local URL Streamlit prints (default http://localhost:8501).

## Configure

- API keys are loaded from the repo-root `.env` (`GOOGLE_API_KEY`, `GROQ_API_KEY`,
  `OPENAI_API_KEY`, `TAVILY_API_KEY`); copy `.env.example` to start. You only need
  the key for the provider of the model you pick, plus `TAVILY_API_KEY` for web search.
- Everything else is controlled live from the sidebar; changing a setting rebuilds
  the agent and starts a fresh memory thread.

## Files

- `agent_core.py` — the factory that assembles the deep agent from the sidebar
  config (tools, backends, sub-agents, skills, memory, middleware).
- `streamlit_app.py` — the chat UI, conversation memory, and the live plan/file panels.

## Note on the Groq free tier

The free tier caps requests at ~8000 tokens/min. Loading all skills + memory +
the full deep-agent system prompt at once can exceed this and return a `413`.
If that happens, load fewer skills, shorten the system prompt, or stay on
`openai/gpt-oss-20b`. The app catches these errors and shows them inline rather
than crashing.
