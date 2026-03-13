"""
Phase 2, Step 2: Full agent loop.

What you'll learn:
- The complete agent loop pattern
- Handling multiple tool calls in one response
- Feeding tool results back into the conversation
- Agents that chain multiple tool calls to solve a problem
"""

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "The city name"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "calculate",
        "description": "Evaluate a math expression.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression to evaluate"}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "get_time",
        "description": "Get the current time in a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "The city name"}
            },
            "required": ["city"]
        }
    }
]


def get_weather(city: str) -> str:
    data = {"Tokyo": "22°C sunny", "New York": "15°C cloudy", "London": "10°C rainy"}
    return data.get(city, f"No data for {city}")


def calculate(expression: str) -> str:
    try:
        allowed = set("0123456789+-*/()., ")
        if not all(c in allowed for c in expression):
            return "Error: unsafe expression"
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"


def get_time(city: str) -> str:
    times = {"Tokyo": "09:00 JST", "New York": "19:00 EST", "London": "00:00 GMT"}
    return times.get(city, f"No timezone data for {city}")


def call_tool(name: str, inputs: dict) -> str:
    if name == "get_weather":
        return get_weather(**inputs)
    elif name == "calculate":
        return calculate(**inputs)
    elif name == "get_time":
        return get_time(**inputs)
    return f"Unknown tool: {name}"


def run_agent(user_message: str, verbose: bool = True) -> str:
    """
    The core agent loop:
    1. Send message to AI
    2. If AI wants to use a tool, call it and feed result back
    3. Repeat until AI gives a final answer
    """
    messages = [{"role": "user", "content": user_message}]
    step = 0

    while True:
        step += 1
        if verbose:
            print(f"\n--- Step {step} ---")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )

        if verbose:
            print(f"Stop reason: {response.stop_reason}")

        # AI is done — return the final text answer
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        # AI wants to use tools
        if response.stop_reason == "tool_use":
            # Add AI's response to conversation history
            messages.append({"role": "assistant", "content": response.content})

            # Process all tool calls in this response
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if verbose:
                        print(f"Tool call: {block.name}({block.input})")

                    result = call_tool(block.name, block.input)

                    if verbose:
                        print(f"Tool result: {result}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Feed all tool results back into the conversation
            messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    print("=== Agent Loop Demo ===\n")

    queries = [
        "What's the weather in Tokyo?",
        "What is (125 * 4) + 88?",
        "Compare the weather in Tokyo and New York, and tell me which is warmer."
    ]

    for query in queries:
        print(f"\nUser: {query}")
        answer = run_agent(query, verbose=True)
        print(f"\nFinal Answer: {answer}")
        print("=" * 50)
