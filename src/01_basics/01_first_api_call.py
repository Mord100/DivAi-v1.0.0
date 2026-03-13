"""
Phase 1, Step 1: Your first API call with Claude.

What you'll learn:
- How to initialize the Anthropic client
- How to send a message and get a response
- The basic message structure (role: user/assistant)
"""

import anthropic
from dotenv import load_dotenv

load_dotenv()  # Loads ANTHROPIC_API_KEY from your .env file

client = anthropic.Anthropic()

# Simple single-turn message
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Explain AI agents in 3 bullet points"}
    ]
)

print("=== Response ===")
print(message.content[0].text)

print("\n=== Metadata ===")
print(f"Model: {message.model}")
print(f"Input tokens:  {message.usage.input_tokens}")
print(f"Output tokens: {message.usage.output_tokens}")
