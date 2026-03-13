"""
Phase 4, Step 2: LangGraph agent with persistent memory.

What you'll learn:
- Using MemorySaver for in-memory checkpointing
- thread_id to scope conversations
- How the agent remembers previous turns
- Inspecting graph state at any point
"""

import operator
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]


@tool
def remember_fact(fact: str) -> str:
    """Store a fact that the user told you. Confirm it was saved."""
    return f"Saved: {fact}"


tools = [remember_fact]
llm = ChatAnthropic(model="claude-sonnet-4-6").bind_tools(tools)


def agent_node(state: AgentState) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools))
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

# MemorySaver stores conversation history in RAM
# In production, use SqliteSaver or RedisSaver for persistence across restarts
memory = MemorySaver()
app = graph.compile(checkpointer=memory)


def chat(message: str, thread_id: str) -> str:
    """Send a message in a specific conversation thread."""
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config
    )
    return result["messages"][-1].content


if __name__ == "__main__":
    print("=== Conversation with Memory ===\n")

    # Thread 1: Alice's conversation
    print("--- Thread: alice ---")
    r1 = chat("Hi! My name is Alice and I love Python.", thread_id="alice")
    print(f"Turn 1: {r1}\n")

    r2 = chat("What's my name?", thread_id="alice")
    print(f"Turn 2 (should remember Alice): {r2}\n")

    r3 = chat("What programming language did I mention?", thread_id="alice")
    print(f"Turn 3 (should remember Python): {r3}\n")

    # Thread 2: Bob's conversation - completely separate memory
    print("\n--- Thread: bob ---")
    r4 = chat("My name is Bob and I prefer TypeScript.", thread_id="bob")
    print(f"Turn 1: {r4}\n")

    r5 = chat("What's my name?", thread_id="bob")
    print(f"Turn 2 (should say Bob, not Alice): {r5}\n")

    # Back to Alice — memory persists
    print("\n--- Back to Thread: alice ---")
    r6 = chat("Do you still remember my name?", thread_id="alice")
    print(f"Turn 4 (should still say Alice): {r6}\n")

    # Inspect the state of alice's conversation
    config = {"configurable": {"thread_id": "alice"}}
    state = app.get_state(config)
    print(f"\nTotal messages in Alice's conversation: {len(state.values['messages'])}")
