"""
DivAi — SSE Stream Route (Phase 6)

ENDPOINT:
  GET /api/stream/{session_id}

CONCEPT: Server-Sent Events (SSE) — Deep Dive
----------------------------------------------
SSE is an HTTP connection that stays open. The server pushes
data frames whenever it has something to say.

Wire format (what gets sent over the connection):

    data: {"type": "node_complete", "node": "ingestion"}\n\n
    data: {"type": "node_complete", "node": "analysis"}\n\n
    data: {"type": "pipeline_complete"}\n\n

Rules:
  - Each message starts with "data: "
  - Messages end with a BLANK LINE (\\n\\n)
  - The Content-Type must be "text/event-stream"
  - Connection must stay open (no Content-Length header)

The browser's EventSource API reads this stream:
    const es = new EventSource('/api/stream/abc-123')
    es.onmessage = (e) => console.log(JSON.parse(e.data))

CONCEPT: sse-starlette EventSourceResponse
-------------------------------------------
sse-starlette handles the SSE protocol details:
  - Sets Content-Type: text/event-stream
  - Sets Cache-Control: no-cache
  - Keeps connection alive
  - Formats each yield as a proper SSE frame

We just yield dicts: {"data": json_string}
The library handles the "data: ...\n\n" formatting.

CONCEPT: Heartbeat
-------------------
Some proxies/firewalls close idle connections after 30-60 seconds.
If no nodes have run recently, we emit a heartbeat ping every 25 seconds.
The client ignores heartbeats — they only serve to keep the connection alive.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from api.session_store import get_session

router = APIRouter()

HEARTBEAT_INTERVAL = 25   # seconds between keep-alive pings
QUEUE_TIMEOUT = 30        # seconds to wait for next event before heartbeat

NODE_LABELS = {
    "ingestion":    "Scraping website",
    "analysis":     "Analysing business signals",
    "human_review": "Intelligence report ready",
    "use_case":     "Generating use cases",
    "solution":     "Designing solutions",
    "proposal":     "Writing proposal",
}


@router.get("/stream/{session_id}")
async def stream_events(session_id: str):
    """
    SSE endpoint — streams pipeline progress events to the client.

    Returns an EventSourceResponse backed by an async generator.
    The generator:
      1. Waits for events from session.queue (filled by the pipeline thread)
      2. Yields each event as a formatted SSE frame
      3. Sends heartbeats when idle (to keep connection alive)
      4. Closes when it receives the "stream_end" sentinel event

    CONCEPT: Async Generator
    A function with 'yield' is a generator. An async generator uses
    'async def' + 'yield'. It can be awaited between yields, which means
    the event loop can handle other work while the generator is waiting.

    EventSourceResponse wraps our generator and handles the HTTP layer.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    async def generate():
        """
        Async generator that yields SSE events.

        On initial connection: events stream live from the queue.
        On reconnect (user left and came back): we first replay the recorded
        completed_nodes + current pending_interaction so the frontend can
        reconstruct its UI state without having to re-run the pipeline.
        """
        ts = datetime.now().isoformat()

        # ── Replay state for reconnecting clients ─────────────────────────
        # If any nodes have already completed, replay their node_complete events
        # so the frontend can reconstruct the pipeline progress view.
        if session.completed_nodes or session.status not in ("pending", "running"):
            yield {"data": json.dumps({
                "type": "pipeline_start",
                "message": f"Reconnected to pipeline for {session.url}",
                "url": session.url,
                "depth": session.depth,
                "timestamp": ts,
            })}

            for node_name in session.completed_nodes:
                yield {"data": json.dumps({
                    "type": "node_complete",
                    "node": node_name,
                    "label": NODE_LABELS.get(node_name, node_name),
                    "stage": node_name,
                    "data": None,   # report page loads full data from its own API call
                    "timestamp": ts,
                })}

            # If pipeline finished, close the stream immediately
            if session.status == "complete":
                proposal_title = None
                if session.final_state:
                    proposal_title = (session.final_state.get("proposal_paths") or {}).get("title")
                yield {"data": json.dumps({
                    "type": "pipeline_complete",
                    "message": "Pipeline complete. Report is ready.",
                    "proposal_title": proposal_title,
                    "timestamp": ts,
                })}
                yield {"data": json.dumps({"type": "stream_end", "timestamp": ts})}
                return

            if session.status == "error":
                yield {"data": json.dumps({
                    "type": "error",
                    "message": session.error or "Pipeline error",
                    "timestamp": ts,
                })}
                yield {"data": json.dumps({"type": "stream_end", "timestamp": ts})}
                return

            # If awaiting user input, re-emit the interaction prompt.
            # Then fall through to the queue loop — when the user submits their
            # selection the pipeline thread unblocks and emits new events.
            if session.status == "awaiting_input" and session.pending_interaction:
                interaction = session.pending_interaction
                interaction_type = interaction.get("type", "select_use_cases")
                yield {"data": json.dumps({
                    "type": "interaction_required",
                    "interaction_type": interaction_type,
                    "data": {
                        "use_cases": interaction.get("use_cases"),
                        "solutions": interaction.get("solutions"),
                        "message": (
                            "Select which use cases to build solutions for."
                            if interaction_type == "select_use_cases"
                            else "Select the solution to build."
                        ),
                    },
                    "timestamp": ts,
                })}

        # ── Normal streaming loop ─────────────────────────────────────────
        # If the session already completed before client connected,
        # drain any buffered events then close
        while True:
            try:
                # Wait up to QUEUE_TIMEOUT seconds for the next event
                event = await asyncio.wait_for(
                    session.queue.get(),
                    timeout=QUEUE_TIMEOUT
                )

                # Yield event as SSE frame
                # sse-starlette format: {"data": "string to send as SSE data"}
                yield {"data": json.dumps(event)}

                # CONCEPT: Sentinel — detecting end of stream
                # The pipeline_runner emits {"type": "stream_end"} when done.
                # When we see it, break the loop → generator returns → connection closes.
                if event.get("type") == "stream_end":
                    break

            except asyncio.TimeoutError:
                # No event for QUEUE_TIMEOUT seconds → send heartbeat
                heartbeat = {
                    "type": "heartbeat",
                    "status": session.status,
                }
                yield {"data": json.dumps(heartbeat)}

                # If session is done but we never got stream_end (edge case), stop
                if session.status in ("complete", "error"):
                    break

            except Exception as e:
                # Unexpected error in the generator itself
                yield {"data": json.dumps({"type": "error", "message": str(e)})}
                break

    return EventSourceResponse(generate())
