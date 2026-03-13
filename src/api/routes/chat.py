"""
DivAi — Proposal Chat Endpoint (Phase 6+)

CONCEPT: In-Context Chat (no RAG needed here)
----------------------------------------------
The full proposal is ~3-5k tokens — well within Claude's 200k context window.
So instead of vector search, we drop the entire proposal into the system prompt.
Claude can reason over ALL of it with no retrieval errors and no chunking.

CONCEPT: Tool Use for Structured Edits
-----------------------------------------
Plain text responses are fine for Q&A. But when the user asks to edit a section,
we need to know: which section? what new content? Tool use gives us that structure.

  user:   "Make the executive summary shorter"
  Claude: <tool_call>update_section(section="executive_summary", content="…")</tool_call>

The tool result is streamed as a separate SSE event type so the frontend can
update the live proposal preview without a page reload.

CONCEPT: Streaming Tool Use Events
--------------------------------------
Anthropic streams tool use in three steps:
  1. content_block_start  — tells us a tool_use block is starting + gives tool name
  2. content_block_delta  — streams the input JSON incrementally (partial_json chunks)
  3. content_block_stop   — block is complete; we now have the full JSON to parse

We accumulate the partial_json in `current_tool_input`, parse it on block_stop,
then emit a section_update SSE event to the frontend.

CONCEPT: current_content — Live State as Context
--------------------------------------------------
Each chat request sends the CURRENT proposal content (which may include previous
edits made in this chat session). This way Claude always works from the latest
version of the document, not the original pipeline output.
"""

import json
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from anthropic import Anthropic
from dotenv import load_dotenv

from api.session_store import get_session

load_dotenv()

router = APIRouter()
client = Anthropic()

# Sections the AI is allowed to edit (text fields only — tables/lists are excluded
# from direct editing to avoid type-mismatch errors in the frontend renderer).
EDITABLE_SECTIONS = [
    "executive_summary",
    "problem_statement",
    "proposed_architecture",
    "investment_summary",
    "api_specifications",
    "security_compliance",
    "testing_strategy",
    "deployment_devops",
]

UPDATE_SECTION_TOOL = {
    "name": "update_section",
    "description": (
        "Update a specific section of the proposal. "
        "Call this when the user asks to edit, rewrite, improve, shorten, expand, "
        "or change any part of the proposal text. "
        "Always call this tool when making edits — do not just write the new content as plain text."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "section": {
                "type": "string",
                "enum": EDITABLE_SECTIONS,
                "description": "Which section of the proposal to update.",
            },
            "content": {
                "type": "string",
                "description": "The full new text for this section.",
            },
        },
        "required": ["section", "content"],
    },
}


# ── Pydantic models ──────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str       # "user" | "assistant"
    content: str


class ChatPayload(BaseModel):
    message: str
    history: list[ChatMessage] = []
    # The frontend sends the live proposal content (may include previous edits)
    # so Claude always works from the latest version.
    current_content: Optional[dict] = None


# ── System prompt builder ────────────────────────────────────────────────────

def _build_system_prompt(final_state: dict, current_content: Optional[dict]) -> str:
    """
    Build a context-rich system prompt from the session's final state.

    CONCEPT: We use the current_content from the frontend if provided — this
    ensures Claude sees any edits made earlier in the chat session, not just
    the original pipeline output.
    """
    proposal = final_state.get("proposal_paths") or {}
    # Live state takes priority so edits are reflected in future responses
    content = current_content or proposal.get("content") or {}
    report = final_state.get("intelligence_report") or {}

    lines = [
        "You are a proposal editing assistant for DivAi.",
        "You help sales and delivery teams refine AI-powered software development proposals.",
        "",
        "Rules:",
        "- Answer questions directly and concisely.",
        "- When asked to edit any section, call update_section with the complete new text.",
        "  Do not write the edited content as plain text — always use the tool.",
        "- Keep all edits professional, client-facing, and grounded in the proposal context.",
        "- Do not invent facts not present in the proposal or intelligence report.",
        "- IMPORTANT: Respond in plain text only. No markdown — no **, no ##, no ---, no backticks.",
        "  Use plain numbered lists (1. 2. 3.) or plain prose. Never use markdown syntax.",
        "",
        f"## Proposal: {proposal.get('title', 'Untitled')}",
        f"**Client:** {proposal.get('client', 'Unknown')}",
        "",
    ]

    section_labels = [
        ("executive_summary",    "Executive Summary"),
        ("problem_statement",    "Problem Statement"),
        ("proposed_architecture","Proposed Architecture"),
        ("api_specifications",   "API Specifications"),
        ("security_compliance",  "Security & Compliance"),
        ("testing_strategy",     "Testing Strategy"),
        ("deployment_devops",    "Deployment & DevOps"),
        ("investment_summary",   "Investment Summary"),
    ]
    for key, label in section_labels:
        val = content.get(key)
        if val:
            lines.append(f"### {label}\n{val}\n")

    stack = content.get("stack_choices")
    if stack:
        lines.append("### Technology Stack")
        lines.extend(f"- {s}" for s in stack)
        lines.append("")

    phases = content.get("phase_details")
    if phases:
        lines.append("### Delivery Phases")
        for i, p in enumerate(phases, 1):
            lines.append(f"{i}. {p}")
        lines.append("")

    # Business context gives Claude grounding for fact-checking edits
    if report:
        lines += [
            "## Business Intelligence",
            f"**Category:** {report.get('business_category', 'Unknown')}",
        ]
        features = report.get("key_features", [])
        if features:
            lines.append(f"**Key Features:** {', '.join(features[:8])}")
        notes = report.get("analyst_notes")
        if notes:
            lines.append(f"**Analyst Notes:** {notes}")

    return "\n".join(lines)


# ── Streaming generator ──────────────────────────────────────────────────────

async def _stream_chat(payload: ChatPayload, final_state: dict):
    """
    Run Claude in a thread pool and yield SSE-formatted events.

    SSE event types:
      {"type": "delta",          "text": "..."}         — streaming text chunk
      {"type": "section_update", "section": "...",
       "content": "..."}                                — proposal edit from tool use
      {"type": "done"}                                  — stream complete
      {"type": "error",          "message": "..."}      — unexpected error
    """
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    system_prompt = _build_system_prompt(final_state, payload.current_content)

    # Build Anthropic messages list from history + new user message
    messages = [{"role": m.role, "content": m.content} for m in payload.history]
    messages.append({"role": "user", "content": payload.message})

    def run_claude():
        """
        Runs synchronously in a thread pool.
        Bridges events back to the async world via loop.call_soon_threadsafe().
        """
        try:
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=system_prompt,
                tools=[UPDATE_SECTION_TOOL],
                messages=messages,
            ) as stream:
                current_tool_name: Optional[str] = None
                current_tool_input = ""

                for event in stream:
                    etype = event.type

                    if etype == "content_block_start":
                        block = event.content_block
                        if block.type == "tool_use":
                            # A tool call is starting — record which tool
                            current_tool_name = block.name
                            current_tool_input = ""

                    elif etype == "content_block_delta":
                        delta = event.delta
                        if delta.type == "text_delta" and delta.text:
                            # Regular text chunk — stream to frontend
                            loop.call_soon_threadsafe(
                                queue.put_nowait,
                                {"type": "delta", "text": delta.text}
                            )
                        elif delta.type == "input_json_delta":
                            # Tool input arriving in chunks — accumulate
                            current_tool_input += delta.partial_json

                    elif etype == "content_block_stop":
                        # A tool call block just finished — parse and emit
                        if current_tool_name == "update_section" and current_tool_input:
                            try:
                                tool_data = json.loads(current_tool_input)
                                loop.call_soon_threadsafe(
                                    queue.put_nowait,
                                    {
                                        "type": "section_update",
                                        "section": tool_data.get("section"),
                                        "content": tool_data.get("content"),
                                    }
                                )
                            except (json.JSONDecodeError, KeyError):
                                pass
                            current_tool_name = None
                            current_tool_input = ""

        except Exception as e:
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {"type": "error", "message": str(e)}
            )
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

    loop.run_in_executor(None, run_claude)

    # Drain the queue and yield SSE events
    while True:
        event = await queue.get()
        if event is None:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            break
        yield f"data: {json.dumps(event)}\n\n"


# ── Route ────────────────────────────────────────────────────────────────────

@router.post("/chat/{session_id}")
async def chat(session_id: str, payload: ChatPayload):
    """
    Stream a chat response about a proposal.

    Body:  { "message": "...", "history": [...], "current_content": {...} }
    Stream: text/event-stream
      data: {"type": "delta", "text": "..."}
      data: {"type": "section_update", "section": "...", "content": "..."}
      data: {"type": "done"}
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.final_state:
        raise HTTPException(status_code=409, detail="Pipeline not yet complete — no proposal to chat about")

    return StreamingResponse(
        _stream_chat(payload, session.final_state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering
            "Connection": "keep-alive",
        },
    )
