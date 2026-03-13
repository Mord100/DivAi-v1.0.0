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

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from api.session_store import get_session

router = APIRouter()

HEARTBEAT_INTERVAL = 25   # seconds between keep-alive pings
QUEUE_TIMEOUT = 30        # seconds to wait for next event before heartbeat


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

        CONCEPT: asyncio.wait_for()
        queue.get() is a coroutine that waits until an item is available.
        If the pipeline is slow, it could wait indefinitely.
        asyncio.wait_for(coroutine, timeout=N) adds a timeout:
          - If the event arrives within N seconds → return it
          - If not → raise asyncio.TimeoutError → we send a heartbeat instead
        """
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
