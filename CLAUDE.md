# DivAi — Claude Code Instructions

## Project Overview

**DivAi** is an AI-powered business intelligence platform that turns any website into a qualified
software development lead with a ready-to-build technical proposal in under 5 minutes..

**Architecture:** Multi-agent LangGraph pipeline → FastAPI backend → Next.js/TypeScript frontend

**Full spec:** See `AI_DEVELOPMENT_GUIDE.md` and `DivAi_Architecture.docx` for complete design.

---

## LEARNING MODE — Always On

This is a **learning project**. The primary goal is for the developer to deeply understand every
concept, pattern, and tool used — not just to ship working code.

### Rules for every response:

1. **Explain before you code**
   Before writing any code, explain:
   - What concept or pattern we are implementing
   - Why this approach is used (not just what it does)
   - How it fits into the broader DivAi architecture
   - What alternatives exist and why we chose this one

2. **Define every new term on first use**
   When a new AI/ML concept, framework concept, or architectural pattern appears for the
   first time (e.g. "embeddings", "cosine similarity", "stateful graph", "checkpointing",
   "tool use"), explain it in plain language with a one-line analogy before proceeding.

3. **Connect code to the big picture**
   After writing code, always explain:
   - Which layer of the DivAi architecture this belongs to (Ingestion / Intelligence / Solution / Proposal)
   - Which phase of the delivery roadmap we are in
   - How this piece connects to adjacent agents/components

4. **Explain every non-obvious line**
   Add inline comments for anything that is not immediately obvious to a learner.
   Do not leave "magic" lines unexplained.

5. **Highlight the AI-specific reasoning**
   When making decisions that are specific to AI development (e.g. chunking strategy,
   temperature settings, prompt design, graph routing logic), call them out explicitly
   and explain the trade-offs.

6. **Use analogies freely**
   Complex AI concepts should be grounded with real-world analogies.
   Example: "A vector embedding is like GPS coordinates for meaning — similar meanings
   land near each other in the vector space, just like nearby places on a map."

7. **Checkpoint understanding**
   At the end of major code sections (completing an agent, a RAG pipeline, a graph),
   provide a short "What you just learned" summary listing the key concepts covered.

8. **Flag when patterns repeat**
   When we implement something that follows a pattern from the AI Development Guide
   (e.g. "this is the same agent loop from Phase 2"), call it out so the developer
   builds pattern recognition.

9. **Warn before complexity jumps**
   If a task introduces significant new complexity, say so upfront and optionally
   suggest breaking it into smaller steps.

10. **Never just give a code dump**
    Code without explanation is not acceptable in this project. Every piece of code
    must be understood, not just copied.

---

## DivAi Architecture Reference

### Agents (LangGraph nodes)
| Agent | Role |
|---|---|
| Ingestion Agent | Playwright scraper — DOM + network traffic |
| Analysis Agent | Classifies tech stack, APIs, auth patterns |
| Use Case Agent | Generates ranked business opportunities (RAG) |
| Solution Agent | Matches use cases to solution blueprints (RAG) |
| Proposal Agent | Generates .docx / .pdf / Notion proposals |
| Supervisor Agent | Orchestrates routing, retries, human-in-the-loop |

### Delivery Phases
| Phase | Focus | Weeks |
|---|---|---|
| 1 | Ingestion Agent + Direct API calls | 1–2 |
| 2 | Analysis Agent + Tool Use | 3–4 |
| 3 | Use Case + Solution Agents (LangChain + RAG) | 5–6 |
| 4 | LangGraph Orchestration (full graph) | 7–8 |
| 5 | Proposal Generation + Exports | 9–10 |
| 6 | FastAPI + Next.js Frontend | 11–14 |
| 7 | Production + Monitoring + Launch | 15–16 |

### Shared State
All agents share `DivAiState` (TypedDict). Key fields:
- `target_url`, `scrape_depth` — input
- `raw_dom`, `network_log` — from Ingestion Agent
- `intelligence_report` — from Analysis Agent
- `use_cases`, `solutions` — from Use Case / Solution Agents
- `proposal_paths` — from Proposal Agent
- `current_stage`, `error` — control flow

### Tech Stack Summary
- **LLM:** Claude (claude-sonnet-4-6) via Anthropic SDK
- **Orchestration:** LangGraph stateful graph
- **Chains:** LangChain (LCEL, tools, prompts)
- **Vector DB:** ChromaDB (dev), Pinecone (prod)
- **Scraping:** Playwright (headless browser)
- **Backend:** FastAPI + PostgreSQL + Redis
- **Frontend:** Next.js 14 + TypeScript + Anthropic TS SDK
- **Documents:** python-docx + WeasyPrint + Notion API
- **Monitoring:** LangSmith

---

## Development Guidelines

### Code style
- Python: type hints everywhere, Pydantic models for all data, async/await for I/O
- TypeScript: strict mode, Zod schemas mirror Pydantic models
- Comments: explain the "why", not the "what"

### Current working directory
`C:/Users/ching/Documents/DiV Dynamics/DivAi`

### Virtual environment
Activate before running: `venv/Scripts/activate`
Run scripts: `venv/Scripts/python src/...`

### Environment variables
Copy `.env.example` to `.env`. Required: `ANTHROPIC_API_KEY`

### File structure
```
src/
├── 01_basics/         Phase 1 learning examples
├── 02_agents/         Phase 2 learning examples
├── 03_langchain/      Phase 3 learning examples
├── 04_langgraph/      Phase 4 learning examples
├── 05_rag/            Phase 5 learning examples
├── agents/            DivAi production agents (built during project)
├── state/             DivAiState schema
├── api/               FastAPI backend (Phase 6)
└── rag/               DivAi RAG pipelines (Phase 3+)
```
