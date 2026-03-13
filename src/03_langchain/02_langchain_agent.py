"""
Phase 3, Step 2: LangChain agents with tools.

What you'll learn:
- Defining tools with the @tool decorator
- Creating a tool-calling agent
- Using AgentExecutor to run the agent loop
- Verbose mode to see the agent's reasoning
"""

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

load_dotenv()

llm = ChatAnthropic(model="claude-sonnet-4-6")


# --- Define tools using the @tool decorator ---
# The docstring becomes the tool's description — write it clearly!

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers together."""
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Add two integers together."""
    return a + b


@tool
def get_word_count(text: str) -> int:
    """Count the number of words in a text string."""
    return len(text.split())


@tool
def reverse_string(text: str) -> str:
    """Reverse a string."""
    return text[::-1]


tools = [multiply, add, get_word_count, reverse_string]

# --- Build the agent ---
# The {agent_scratchpad} placeholder is required — it's where tool calls get inserted
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Use tools when needed to answer accurately."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def ask(question: str):
    print(f"\nQuestion: {question}")
    print("-" * 40)
    result = executor.invoke({"input": question})
    print(f"\nAnswer: {result['output']}")
    print("=" * 50)


if __name__ == "__main__":
    ask("What is 42 multiplied by 7?")
    ask("Add 150 and 75, then multiply the result by 3.")
    ask("How many words are in the phrase 'The quick brown fox jumps over the lazy dog'?")
    ask("Reverse the word 'LangChain'.")
