# AI Development Guide
## Build AI Agents with Python, TypeScript, LangChain, LangGraph & RAG

---

## Table of Contents

1. [Phase 1 - Foundations](#phase-1-foundations)
2. [Phase 2 - Building Agents](#phase-2-building-agents)
3. [Phase 3 - LangChain](#phase-3-langchain)
4. [Phase 4 - LangGraph](#phase-4-langgraph)
5. [Phase 5 - RAG](#phase-5-rag-retrieval-augmented-generation)
6. [Phase 6 - TypeScript](#phase-6-typescript)
7. [Phase 7 - Production Patterns](#phase-7-production-patterns)
8. [Learning Path](#recommended-learning-path)
9. [Resources](#resources)

---

## Project Structure

```
DivAi/
├── AI_DEVELOPMENT_GUIDE.md       <- This file
├── .env.example                  <- Copy to .env and add your API keys
├── requirements.txt              <- Python dependencies
├── src/
│   ├── 01_basics/
│   │   ├── 01_first_api_call.py
│   │   └── 02_prompt_engineering.py
│   ├── 02_agents/
│   │   ├── 01_tool_use.py
│   │   └── 02_agent_loop.py
│   ├── 03_langchain/
│   │   ├── 01_basic_chain.py
│   │   └── 02_langchain_agent.py
│   ├── 04_langgraph/
│   │   ├── 01_basic_graph.py
│   │   └── 02_memory_graph.py
│   └── 05_rag/
│       ├── 01_basic_rag.py
│       └── 02_agentic_rag.py
```

---

## Phase 1: Foundations

### Step 1 - Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# Install core dependencies
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your API key:
```
ANTHROPIC_API_KEY=your_key_here
```

Get your key at: https://console.anthropic.com

### Step 2 - First API Call

**File:** `src/01_basics/01_first_api_call.py`

```python
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Explain AI agents in simple terms"}
    ]
)

print(message.content[0].text)
```

**Run it:**
```bash
python src/01_basics/01_first_api_call.py
```

### Step 3 - Prompt Engineering

Key techniques to master:

| Technique | What it does |
|---|---|
| **System prompts** | Set the AI's role and persona |
| **Few-shot examples** | Show the AI examples of desired output |
| **Chain of Thought** | Ask AI to "think step by step" |
| **Output formatting** | Request JSON, markdown, or structured data |

**File:** `src/01_basics/02_prompt_engineering.py`

```python
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

# JSON output formatting
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="You are a JSON-only response bot. Always respond with valid JSON.",
    messages=[
        {"role": "user", "content": "List 3 programming languages with their use cases"}
    ]
)

print(message.content[0].text)
```

---

## Phase 2: Building Agents

### What is an AI Agent?

An agent is an LLM that can:
1. **Reason** — think through problems
2. **Use tools** — call functions, search the web, run code
3. **Act in a loop** — keep going until the task is complete

```
User Input → LLM thinks → Decides to use a tool → Gets result → Thinks again → Final answer
```

### Step 4 - Tool Use / Function Calling

**File:** `src/02_agents/01_tool_use.py`

The AI can call functions you define. You:
1. Describe the tools in JSON schema format
2. Implement the actual function logic
3. Run an agent loop that processes tool calls

### Step 5 - Agent Loop

**File:** `src/02_agents/02_agent_loop.py`

The core pattern:
```
while True:
    response = llm.invoke(messages)
    if response.stop_reason == "end_turn":
        return response  # Done
    if response.stop_reason == "tool_use":
        result = call_tool(response.tool_name, response.tool_input)
        messages.append(result)  # Feed result back, loop again
```

---

## Phase 3: LangChain

LangChain is a framework that abstracts common AI patterns with reusable components.

### Core Concepts

| Concept | Description |
|---|---|
| **LLM / ChatModel** | Wrapper around any AI model API |
| **Prompt Templates** | Reusable, parameterized prompts |
| **Output Parsers** | Extract structured data from responses |
| **Chains (LCEL)** | Pipe components together with `\|` operator |
| **Tools** | Functions the agent can call |
| **Agents** | LLM that decides which tools to use |

### Step 6 - Basic Chain

**File:** `src/03_langchain/01_basic_chain.py`

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatAnthropic(model="claude-sonnet-4-6")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert in {topic}"),
    ("human", "{question}")
])

# Chain: prompt -> llm -> parse output as string
chain = prompt | llm | StrOutputParser()

result = chain.invoke({
    "topic": "Python programming",
    "question": "What are decorators?"
})
print(result)
```

### Step 7 - LangChain Agent with Tools

**File:** `src/03_langchain/02_langchain_agent.py`

Use the `@tool` decorator to define tools, then wire them into an agent executor.

---

## Phase 4: LangGraph

LangGraph lets you build agents as **stateful graphs** where:
- **Nodes** are functions that process state
- **Edges** control the flow between nodes
- **State** is passed and updated at each step

### Why LangGraph over simple agents?

| Feature | Simple Agent | LangGraph |
|---|---|---|
| Conditional branching | Hard | Built-in |
| Loops | Manual | Built-in |
| Human-in-the-loop | Very hard | Built-in |
| Multi-agent systems | Hard | Built-in |
| Memory / checkpointing | Manual | Built-in |
| Visualizing flow | No | Yes |

### Step 8 - Basic LangGraph Agent

**File:** `src/04_langgraph/01_basic_graph.py`

```
[START] --> [agent node] --> should_continue?
                                |
                    yes: tool_calls --> [tools node] --> back to [agent node]
                    no:  end_turn   --> [END]
```

### Step 9 - LangGraph with Memory

**File:** `src/04_langgraph/02_memory_graph.py`

Use `MemorySaver` to persist conversation history across turns:

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = graph.compile(checkpointer=memory)

# thread_id scopes the memory to one conversation
config = {"configurable": {"thread_id": "user-123"}}
app.invoke({"messages": [HumanMessage("My name is Alice")]}, config)
app.invoke({"messages": [HumanMessage("What's my name?")]}, config)
# -> "Your name is Alice"
```

---

## Phase 5: RAG (Retrieval Augmented Generation)

### What is RAG?

RAG lets your AI answer questions from **your own documents** without retraining.

```
INDEXING (one-time setup):
  Documents --> Chunk --> Embed --> Vector DB

QUERYING (every request):
  User Query --> Embed --> Search Vector DB --> Relevant Chunks --> LLM --> Answer
```

### Why RAG?

- LLMs have a knowledge cutoff date — RAG adds real-time knowledge
- LLMs can hallucinate — RAG grounds answers in real documents
- Context windows are limited — RAG retrieves only what's relevant
- Cheaper than fine-tuning

### Step 10 - Basic RAG Pipeline

**File:** `src/05_rag/01_basic_rag.py`

Key components:
1. **Document loader** — load PDFs, web pages, text files
2. **Text splitter** — chunk large documents
3. **Embeddings** — convert text to vectors
4. **Vector store** — store and search vectors (ChromaDB)
5. **Retriever** — find relevant chunks
6. **Chain** — retrieve + generate

### Step 11 - Agentic RAG

**File:** `src/05_rag/02_agentic_rag.py`

Combine RAG with LangGraph so the agent can decide *when* to retrieve vs. answer from memory. Supports multi-step reasoning with document lookup.

---

## Phase 6: TypeScript

For web and full-stack AI apps.

### Setup

```bash
mkdir ts-agent && cd ts-agent
npm init -y
npm install @anthropic-ai/sdk dotenv
npm install -D typescript @types/node ts-node
npx tsc --init
```

### Key Difference from Python

TypeScript uses the same patterns but with:
- `async/await` everywhere (same as Python)
- `zod` for schema validation (like Pydantic)
- `@langchain/langgraph` for LangGraph
- Strong typing catches errors at compile time

---

## Phase 7: Production Patterns

### Multi-Agent Systems

```
Supervisor Agent
    |-- Research Agent  (web search, RAG retrieval)
    |-- Code Agent      (writes and executes code)
    |-- Writer Agent    (formats final output)
```

Each agent is a specialized LangGraph subgraph. The supervisor routes tasks to the right specialist.

### Key Production Tools

| Tool | Purpose |
|---|---|
| **LangSmith** | Trace, debug, and evaluate LLM calls |
| **ChromaDB** | Local vector database (dev/small scale) |
| **Pinecone / Weaviate** | Cloud vector database (production) |
| **FastAPI** | Serve your agent as a REST API |
| **Redis** | Persistent memory and checkpointing |
| **Docker** | Containerize your agent for deployment |
| **LangServe** | Deploy LangChain chains as APIs |

### Streaming Responses

```python
# Stream tokens as they generate (better UX)
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Structured Output with Pydantic

```python
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic

class Movie(BaseModel):
    title: str
    year: int
    genre: str
    rating: float

llm = ChatAnthropic(model="claude-sonnet-4-6")
structured_llm = llm.with_structured_output(Movie)

movie = structured_llm.invoke("Tell me about The Matrix")
print(movie.title)   # "The Matrix"
print(movie.year)    # 1999
```

---

## Recommended Learning Path

```
Week 1:   Direct API calls (Phase 1)
          -> Run src/01_basics/ examples

Week 2:   Tool use and basic agents (Phase 2)
          -> Run src/02_agents/ examples

Week 3:   LangChain chains and agents (Phase 3)
          -> Run src/03_langchain/ examples

Week 4:   LangGraph stateful agents (Phase 4)
          -> Run src/04_langgraph/ examples

Week 5:   RAG pipeline (Phase 5)
          -> Run src/05_rag/ examples

Week 6:   TypeScript agents (Phase 6)
          -> Build a simple web-facing agent

Week 7+:  Multi-agent systems, production deployment
```

---

## Resources

| Resource | URL |
|---|---|
| Anthropic API Docs | https://docs.anthropic.com |
| Anthropic Console (get API key) | https://console.anthropic.com |
| LangChain Python Docs | https://python.langchain.com |
| LangGraph Docs | https://langchain-ai.github.io/langgraph |
| LangSmith (tracing) | https://smith.langchain.com |
| DeepLearning.AI Free Courses | https://learn.deeplearning.ai |
| ChromaDB Docs | https://docs.trychroma.com |

---

*This guide is part of the DivAi learning project.*
