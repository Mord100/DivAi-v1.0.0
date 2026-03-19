"""
Phase 2, Step 1: Tool use / function calling.

What you'll learn:
- How to define tools with JSON schema
- How the AI decides when to call a tool
- How to execute the tool and return results
- The tool_use / tool_result message flow.
"""

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

# --- Define the tools the AI can use ---
tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a given city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name, e.g. Tokyo"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "calculate",
        "description": "Evaluate a simple math expression.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A math expression, e.g. '(10 + 5) * 3'"
                }
            },
            "required": ["expression"]
        }
    }
]


# --- Implement the actual tool functions ---
def get_weather(city: str) -> str:
    # In a real app, you'd call a weather API here
    weather_data = {
        "Tokyo": "22°C, partly cloudy",
        "New York": "15°C, sunny",
        "London": "12°C, rainy",
    }
    return weather_data.get(city, f"Weather data not available for {city}")


def calculate(expression: str) -> str:
    try:
        # Only allow safe math operations
        allowed = set("0123456789+-*/()., ")
        if not all(c in allowed for c in expression):
            return "Error: Only basic math operators allowed"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def call_tool(name: str, inputs: dict) -> str:
    if name == "get_weather":
        return get_weather(**inputs)
    elif name == "calculate":
        return calculate(**inputs)
    return f"Unknown tool: {name}"


# --- Single tool call example ---
def demo_single_tool_call():
    print("=== Single Tool Call ===")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=tools,
        messages=[{"role": "user", "content": "What's the weather in Tokyo?"}]
    )

    print(f"Stop reason: {response.stop_reason}")

    for block in response.content:
        if block.type == "tool_use":
            print(f"\nAI wants to call: {block.name}")
            print(f"With inputs: {block.input}")

            result = call_tool(block.name, block.input)
            print(f"Tool result: {result}")


if __name__ == "__main__":
    demo_single_tool_call()
