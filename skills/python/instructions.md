# Python — Detailed Instructions

Detailed, opinionated guidance for producing high-quality Python. Pairs with the
short checklist in `instruction.md` and the code in `examples.md`.

## 1. Environment & packaging (this project uses `uv`)

- `uv init` scaffolds a project; `uv add <pkg>` / `uv remove <pkg>` manage deps and keep
  `pyproject.toml` and `uv.lock` in sync.
- `uv sync` reproduces the exact locked environment. `uv run <cmd>` executes inside it
  without manually activating a venv.
- Pin a Python version with `.python-version` (already present here).
- For libraries you publish, declare `requires-python`, dependencies, and optional
  extras in `[project]` of `pyproject.toml`.

## 2. Typing

- Use builtin generics: `list[int]`, `dict[str, Any]`, not `List`/`Dict` from `typing`.
- Use `X | None` instead of `Optional[X]`; `X | Y` instead of `Union`.
- Prefer `@dataclass(slots=True, frozen=True)` for value objects; `TypedDict` for
  structured dicts; `Protocol` for structural (duck) typing.
- Use `typing.Self` for fluent/builder return types; `assert_never` for exhaustiveness.
- Run `mypy --strict` (or pyright strict) on library code. Add `# type: ignore[code]`
  only with the specific error code and a reason.

## 3. Idioms & control flow

- **Pathlib over os.path**: `Path("a") / "b"`, `.read_text()`, `.glob()`.
- **EAFP over LBYL** where natural: `try/except` rather than pre-checking, for things
  like dict access use `.get()` or `try/except KeyError`.
- **Structural pattern matching** (`match`/`case`) for dispatching on shape/variant.
- **Comprehensions** for transforms; **generators** for large/streamed data.
- **`enumerate`, `zip`, `itertools`** instead of index bookkeeping.
- **`functools.cache` / `lru_cache`** for pure expensive functions.

## 4. Errors & logging

- Define a small exception hierarchy per package (`class MyError(Exception)`).
- Catch the narrowest exception; re-raise with `raise ... from err` to preserve cause.
- Use the `logging` module (module-level `logger = logging.getLogger(__name__)`), not
  `print`, in library/app code. Configure handlers only at the app entry point.

## 5. Concurrency

- **I/O-bound** → `asyncio` (`async def`, `await`, `asyncio.gather`, `asyncio.TaskGroup`).
- **CPU-bound** → `concurrent.futures.ProcessPoolExecutor` or `multiprocessing`.
- **Many threads of blocking I/O** → `ThreadPoolExecutor` or `asyncio.to_thread`.
- Never mix blocking calls inside an event loop; offload with `asyncio.to_thread`.

## 6. Testing

- Use `pytest`. Name files `test_*.py`, functions `test_*`.
- Prefer plain `assert`; use fixtures for setup, `parametrize` for table-driven tests.
- Mock external boundaries (network, clock, fs) — keep core logic pure and tested directly.
- Aim for fast, deterministic tests; mark slow/integration tests and run them separately.

## 7. Performance notes

- Profile before optimizing (`cProfile`, `timeit`). Optimize the hot path only.
- Prefer builtin/vectorized ops (`numpy`, `pandas`) over Python loops for numeric work.
- Use generators and `itertools` to avoid materializing large lists.

## 8. Common libraries to reach for

- HTTP: `httpx` (async-capable) or `requests`.
- Data validation / settings: `pydantic` v2.
- CLI: `typer` or `argparse`.
- Dates: `datetime` with `zoneinfo`; `dateutil` if parsing messy input.
- Retry/backoff: `tenacity`.
