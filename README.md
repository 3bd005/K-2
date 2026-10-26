# 🧠 K-2

🚀 **[Try K-2 Live](https://k2.3bd005.dev/)**

K-2 is a deep AI agent built with DeepAgents, LangChain, and LangGraph, featuring a Streamlit chat interface.

## ✨ Key Features

- **Planning:** Creates and maintains a to-do list while working.
- **Virtual File System:** Stores intermediate results in files to manage context.
- **Sub-agents:** Delegates research and structured tasks to specialized agents.
- **Skills & Memory:** Loads knowledge and project context when needed.

## 🚀 Quick Start

```bash
uv sync
cp .env.example .env
uv run streamlit run app/streamlit_app.py
```

Configure your API keys in `.env` before running the app.

**Requirements:** Python 3.14+, Node.js is not required to run the Streamlit app.

## 🔑 API Keys

| Variable | Purpose |
|---|---|
| `GOOGLE_API_KEY` | Gemini models |
| `TAVILY_API_KEY` | Web search |
| `GROQ_API_KEY` | Groq models and demos |
| `OPENAI_API_KEY` | OpenAI models |

## 📂 Project Structure

- `app/` — Streamlit application and agent logic.
- `demos/` — Examples demonstrating agent capabilities.
- `memory/` — Persistent project context.
- `skills/` — On-demand knowledge and instructions.
- `.env.example` — API key template.

## 🛠️ Tech Stack

Python · DeepAgents · LangChain · LangGraph · Streamlit · Tavily · QuickJS · uv

---

**Live Demo:** https://k2.3bd005.dev/
