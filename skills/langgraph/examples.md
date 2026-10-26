# LangGraph — Examples

Runnable patterns the agent can adapt. Assumes `langgraph`, `langchain`, and an LLM
provider package are installed (e.g. `langchain-anthropic`).

## Minimal state graph

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    value: int

def increment(state: State) -> dict:
    return {"value": state["value"] + 1}

builder = StateGraph(State)
builder.add_node("inc", increment)
builder.add_edge(START, "inc")
builder.add_edge("inc", END)
graph = builder.compile()

print(graph.invoke({"value": 1}))  # {'value': 2}
```

## Messages state with a reducer

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class ChatState(TypedDict):
    messages: Annotated[list, add_messages]  # appends instead of overwriting
```

## ReAct tool-calling loop (hand-built)

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic

@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

tools = [add]
model = ChatAnthropic(model="claude-opus-4-8").bind_tools(tools)

class State(TypedDict):
    messages: Annotated[list, add_messages]

def agent(state: State) -> dict:
    return {"messages": [model.invoke(state["messages"])]}

builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)  # -> "tools" or END
builder.add_edge("tools", "agent")
graph = builder.compile()

out = graph.invoke({"messages": [("user", "What is 21 + 21?")]})
print(out["messages"][-1].content)
```

## Persistence with a checkpointer

```python
from langgraph.checkpoint.memory import MemorySaver

graph = builder.compile(checkpointer=MemorySaver())
config = {"configurable": {"thread_id": "user-123"}}

graph.invoke({"messages": [("user", "Hi, I'm Sam")]}, config)
graph.invoke({"messages": [("user", "What's my name?")]}, config)  # remembers
```

## Prebuilt ReAct agent

```python
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic

agent = create_react_agent(ChatAnthropic(model="claude-opus-4-8"), tools=[add])
agent.invoke({"messages": [("user", "add 2 and 5")]})
```

## Conditional routing (custom)

```python
def route(state: State) -> str:
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "end"

builder.add_conditional_edges("agent", route, {"tools": "tools", "end": END})
```

## Streaming

```python
for chunk in graph.stream({"messages": [("user", "add 3 and 4")]},
                          stream_mode="updates"):
    print(chunk)
```

## deepagents (this project)

```python
from deepagents import create_deep_agent

research_subagent = {
    "name": "researcher",
    "description": "Does focused web/document research and returns a short summary.",
    "prompt": "You are a careful researcher. Return only the conclusion.",
    "tools": [],  # give it its own tools
}

agent = create_deep_agent(
    tools=[],  # orchestrator tools
    instructions="You are a deep agent. Plan, use the file system, delegate to subagents.",
    subagents=[research_subagent],
)

agent.invoke({"messages": [("user", "Research X and write notes to a file.")]})
```
