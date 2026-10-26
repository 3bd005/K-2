---
name: python
description: Reference skill for writing, structuring, and debugging idiomatic Python 3.11+ code — covers project setup, typing, async, testing, packaging, and common libraries. Load this when a query involves Python language features, tooling, or standard-library usage.
metadata:
  type: reference
  language: python
  version: "3.11+"
---

# Python Skill

This skill gives the deep agent the context it needs to produce correct, idiomatic,
production-quality Python. Use it whenever a task involves writing or reviewing Python
code, choosing tooling, or explaining Python behavior.

## When to use this skill

- The user asks to write, refactor, or debug Python code.
- A task requires choosing a Python library, runtime, or project layout.
- The agent needs to reason about typing, async/await, packaging, or testing.

## Core principles

- **Target Python 3.11+.** Use modern syntax: `X | None` over `Optional[X]`, structural
  pattern matching where it clarifies, `tomllib` for TOML, exception groups when relevant.
- **Type everything public.** Annotate function signatures and dataclasses; let inference
  handle locals. Run `mypy` or `pyright` in strict mode for libraries.
- **Prefer the standard library** before adding a dependency. Reach for `pathlib`,
  `dataclasses`, `itertools`, `functools`, `collections`, `contextlib` first.
- **Use `uv` for environments and packaging** in this project (see `pyproject.toml`,
  `uv.lock`). Fall back to `pip`/`venv` only when `uv` is unavailable.
- **Fail loudly, early, and specifically.** Raise narrow exceptions; never bare `except:`.
- **Make code testable.** Pure functions, dependency injection over globals, `pytest`.

## Project layout (src layout)

```
myproject/
├── pyproject.toml        # metadata, deps, tool config (ruff, mypy, pytest)
├── uv.lock               # pinned, reproducible dependency graph
├── src/mypkg/
│   ├── __init__.py
│   └── core.py
└── tests/
    └── test_core.py
```

## Tooling baseline

| Concern        | Tool                | Command                       |
|----------------|---------------------|-------------------------------|
| Env / deps     | `uv`                | `uv add <pkg>`, `uv sync`     |
| Lint + format  | `ruff`              | `ruff check . && ruff format` |
| Type check     | `mypy` / `pyright`  | `mypy src`                    |
| Tests          | `pytest`            | `uv run pytest`               |
| Run a script   | `uv run`            | `uv run python main.py`       |

## Cross-references

- See `instruction.md` for the quick checklist the agent should follow.
- See `instructions.md` for detailed how-to guidance and decision trees.
- See `examples.md` for runnable code patterns.
