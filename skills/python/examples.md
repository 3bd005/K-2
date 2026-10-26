# Python — Examples

Runnable, copy-pasteable patterns the agent can adapt.

## Dataclass value object

```python
from dataclasses import dataclass

@dataclass(slots=True, frozen=True)
class Point:
    x: float
    y: float

    def translated(self, dx: float, dy: float) -> "Point":
        return Point(self.x + dx, self.y + dy)
```

## Typed function with narrow errors

```python
from pathlib import Path

class ConfigError(Exception): ...

def load_port(path: Path) -> int:
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as err:
        raise ConfigError(f"config missing: {path}") from err
    try:
        return int(raw)
    except ValueError as err:
        raise ConfigError(f"port not an int: {raw!r}") from err
```

## Structural pattern matching

```python
def area(shape: dict) -> float:
    match shape:
        case {"kind": "circle", "r": r}:
            return 3.14159 * r * r
        case {"kind": "rect", "w": w, "h": h}:
            return w * h
        case _:
            raise ValueError(f"unknown shape: {shape}")
```

## Async I/O with TaskGroup

```python
import asyncio
import httpx

async def fetch(client: httpx.AsyncClient, url: str) -> int:
    resp = await client.get(url)
    return resp.status_code

async def main(urls: list[str]) -> list[int]:
    async with httpx.AsyncClient() as client:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(fetch(client, u)) for u in urls]
    return [t.result() for t in tasks]

# asyncio.run(main(["https://example.com"]))
```

## Offload blocking work from the event loop

```python
import asyncio

def cpu_heavy(n: int) -> int:
    return sum(i * i for i in range(n))

async def run() -> int:
    return await asyncio.to_thread(cpu_heavy, 10_000_000)
```

## Pydantic v2 settings / validation

```python
from pydantic import BaseModel, Field

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    debug: bool = False

cfg = ServerConfig.model_validate({"port": 9000})
```

## Pytest table-driven test

```python
import pytest
from mypkg.core import area

@pytest.mark.parametrize(
    "shape, expected",
    [
        ({"kind": "rect", "w": 2, "h": 3}, 6.0),
        ({"kind": "circle", "r": 1}, pytest.approx(3.14159)),
    ],
)
def test_area(shape, expected):
    assert area(shape) == expected
```

## Typer CLI

```python
import typer

app = typer.Typer()

@app.command()
def greet(name: str, loud: bool = False) -> None:
    msg = f"Hello, {name}!"
    typer.echo(msg.upper() if loud else msg)

if __name__ == "__main__":
    app()
```
