"""
DivAi — Session Store (Phase 6, updated for HITL)

Added threading.Event + interaction fields to support the
human-in-the-loop pause/resume pattern.

CONCEPT: threading.Event as a Pause Gate
------------------------------------------
The pipeline runs in a thread. When it hits a pause point (e.g. after
use_case node), it calls interaction_event.wait() — this BLOCKS the
thread until the event is set.

When the user submits their selections via POST /api/interact/{id},
the FastAPI handler calls interaction_event.set() — this UNBLOCKS
the pipeline thread so it can resume.

This is the standard "gate" pattern for cross-thread synchronisation:
  Pipeline thread:  wait() ← blocks here
  API handler:      set()  ← unblocks it
"""

import asyncio
import threading
import uuid
from typing import Optional
from datetime import datetime


class PipelineSession:
    def __init__(self, session_id: str, url: str, depth: str,
                 loop: asyncio.AbstractEventLoop):
        self.session_id = session_id
        self.url = url
        self.depth = depth
        self.loop = loop

        # SSE event queue — pipeline writes, SSE reads
        self.queue: asyncio.Queue = asyncio.Queue()

        # Lifecycle
        self.status = "pending"           # pending | running | awaiting_input | complete | error
        self.current_stage: Optional[str] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now().isoformat()

        # Final report — set when pipeline finishes
        self.final_state: Optional[dict] = None

        # Human-in-the-loop: pause gate
        # The pipeline thread waits on this event at each interaction point.
        # The interact endpoint sets it to resume.
        self.interaction_event = threading.Event()
        self.interaction_response: Optional[dict] = None    # user's submitted data
        self.pending_interaction: Optional[dict] = None     # what we're waiting for

    def emit(self, event: dict) -> None:
        """Thread-safe event emission into the async SSE queue."""
        self.loop.call_soon_threadsafe(self.queue.put_nowait, event)


_sessions: dict[str, PipelineSession] = {}


def create_session(url: str, depth: str,
                   loop: asyncio.AbstractEventLoop) -> PipelineSession:
    session_id = str(uuid.uuid4())
    session = PipelineSession(session_id, url, depth, loop)
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Optional[PipelineSession]:
    return _sessions.get(session_id)


def list_sessions() -> list[dict]:
    return [
        {
            "session_id": s.session_id,
            "url": s.url,
            "status": s.status,
            "current_stage": s.current_stage,
            "created_at": s.created_at,
        }
        for s in _sessions.values()
    ]
