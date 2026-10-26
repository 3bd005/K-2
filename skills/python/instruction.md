# Python — Quick Instruction Checklist

A short, scannable checklist for the agent. For depth, read `instructions.md`.

## Before writing code
- [ ] Confirm the target Python version (assume 3.11+ unless told otherwise).
- [ ] Check `pyproject.toml` / `uv.lock` for existing deps before adding new ones.
- [ ] Match the surrounding code's style, naming, and import conventions.

## While writing
- [ ] Type-annotate every public function, method, and dataclass field.
- [ ] Use `pathlib.Path`, not `os.path`, for filesystem work.
- [ ] Use f-strings; never `%` or `.format()` for new code.
- [ ] Prefer comprehensions and generators over manual loops when readable.
- [ ] Use context managers (`with`) for files, locks, connections.
- [ ] Raise specific exceptions; never `except:` or `except Exception: pass`.
- [ ] Keep functions small and pure where possible.

## Dependencies & environment
- [ ] Add deps with `uv add <pkg>` (updates `pyproject.toml` + `uv.lock`).
- [ ] Run code with `uv run python ...` so the locked env is used.
- [ ] Never hardcode secrets — read from environment / `.env`.

## Before declaring done
- [ ] `ruff check .` passes (lint) and `ruff format` applied.
- [ ] `mypy src` (or `pyright`) is clean for public APIs.
- [ ] `uv run pytest` passes; new behavior has a test.
- [ ] No leftover debug prints; logging used instead.
