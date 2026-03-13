"""
Phase 1, Step 2: Prompt engineering techniques.

What you'll learn:
- System prompts to set AI persona/role
- Requesting structured JSON output
- Chain-of-thought reasoning
- Multi-turn conversations
"""

import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()


def demo_system_prompt():
    print("=== 1. System Prompts ===")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system="You are a senior Python developer who gives concise, practical answers with code examples.",
        messages=[{"role": "user", "content": "What is a decorator?"}]
    )
    print(message.content[0].text)


def demo_json_output():
    print("\n=== 2. Structured JSON Output ===")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system="You always respond with valid JSON only. No extra text.",
        messages=[{
            "role": "user",
            "content": "List 3 AI frameworks with name, language, and main use case"
        }]
    )
    raw = message.content[0].text
    data = json.loads(raw)
    print(json.dumps(data, indent=2))


def demo_chain_of_thought():
    print("\n=== 3. Chain of Thought ===")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": "Think step by step: If I train a model on 1000 examples per hour, "
                       "and I need 500,000 examples, how many days will it take?"
        }]
    )
    print(message.content[0].text)


def demo_multi_turn():
    print("\n=== 4. Multi-turn Conversation ===")
    messages = [
        {"role": "user", "content": "My favorite programming language is Python."},
        {"role": "assistant", "content": "Great choice! Python is excellent for AI/ML, data science, and scripting."},
        {"role": "user", "content": "What language did I just mention?"}
    ]
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=messages
    )
    print(response.content[0].text)


if __name__ == "__main__":
    demo_system_prompt()
    demo_json_output()
    demo_chain_of_thought()
    demo_multi_turn()
