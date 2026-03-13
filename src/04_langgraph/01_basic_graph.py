"""
Phase 4, Step 1: Basic LangGraph agent.

What you'll learn:
- Defining agent state with TypedDict
- Creating nodes (functions that transform state)
- Adding conditional edges (routing logic)
- Compiling and running a graph
- The agent <-> tools loop in graph form
"""

import operator
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

load_dotenv()


# --- 1. Define State ---
# State is a typed dict that flows through every node.
# The Annotated + operator.add tells LangGraph to append messages (not overwrite).
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]


# --- 2. Define Tools ---
@tool
def calculate(expression: str) -> str:
    """Evaluate a basic math expression like '10 * (5 + 3)'."""
    try:
        allowed = set("0123456789+-*/()., ")
        if not all(c in allowed for c in expression):
            return "Error: only basic math operators allowed"
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    data = {
        "Tokyo": "22°C, partly cloudy",
        "Paris": "18°C, sunny",
        "Sydney": "25°C, clear"
    }
    return data.get(city, f"No weather data for {city}")


tools = [calculate, get_weather]

# --- 3. Set up the LLM with tools bound ---
llm = ChatAnthropic(model="claude-sonnet-4-6").bind_tools(tools)


# --- 4. Define Nodes ---
def agent_node(state: AgentState) -> dict:
    """The agent node: calls the LLM and appends its response."""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """
    Routing function: decides where to go after the agent node.
    Returns 'tools' if the AI made tool calls, or END if it's done.
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


# --- 5. Build the Graph ---
graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools))  # ToolNode auto-executes tool calls

graph.set_entry_point("agent")

# After the agent runs, check whether to call tools or end
graph.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", END: END}
)

# After tools run, always go back to the agent
graph.add_edge("tools", "agent")

app = graph.compile()


def run(question: str):
    print(f"\nQuestion: {question}")
    print("-" * 40)
    result = app.invoke({"messages": [HumanMessage(content=question)]})
    final = result["messages"][-1].content
    print(f"Answer: {final}")
    print(f"Total messages in chain: {len(result['messages'])}")


if __name__ == "__main__":
    run("What is (256 * 4) + 100?")
    run("What's the weather like in Tokyo and Paris?")
    run("What is 15 * 15, and what's the weather in Sydney?")
