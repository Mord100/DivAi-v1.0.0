"""
DivAi — Scan Routes (Phase 6)

ENDPOINTS:
  POST /api/scan               — start a pipeline run
  GET  /api/status/{session_id} — lightweight status poll
  GET  /api/sessions           — list all sessions (debug)

CONCEPT: POST vs GET
---------------------
  POST /api/scan — creates a new resource (a pipeline session)
                   Request body carries data (url, depth)
                   Returns the new resource's ID
  GET  /api/status/{id} — reads a resource
                   No body — parameters in the URL path

HTTP method choice is semantic: POST = create, GET = read.
"""

import asyncio
import sys
import os

from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from api.models import ScanRequest, ScanResponse, SessionStatus
from api.session_store import create_session, get_session, list_sessions
from api.pipeline_runner import run_pipeline_in_thread

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /api/scan — start the pipeline
# ---------------------------------------------------------------------------

@router.post("/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest):
    """
    Start a DivAi pipeline run for the given URL.

    CONCEPT: asyncio.create_task() — Fire and Forget
    The pipeline takes ~60 seconds. We don't make the client wait.
    Instead:
      1. Create a session (instant)
      2. Launch the pipeline as a background asyncio task (non-blocking)
      3. Return the session_id immediately (< 1ms response time)
      4. Client connects to SSE stream to watch progress

    asyncio.create_task() schedules a coroutine to run on the event loop
    concurrently. It doesn't await it — it returns immediately.
    The task runs independently until it completes.

    This is different from BackgroundTasks (FastAPI's version, designed
    for cleanup after a response). create_task() is for concurrent work
    that runs alongside other requests.

    CONCEPT: run_in_executor for Sync Code
    run_pipeline_in_thread() is a synchronous function (it calls the
    blocking LangGraph pipeline). We wrap it in run_in_executor() so
    it runs in a thread pool, not on the event loop.

    If we ran it directly on the event loop, the entire server would
    freeze for 60 seconds while the pipeline runs.
    """
    loop = asyncio.get_running_loop()
    session = create_session(request.url, request.depth, loop)

    # CONCEPT: Wrapping sync work as async
    # run_in_executor runs sync fn in a thread → returns a coroutine
    # create_task schedules that coroutine → it runs concurrently
    async def run_pipeline_async():
        await loop.run_in_executor(None, run_pipeline_in_thread, session)

    asyncio.create_task(run_pipeline_async())

    base_url = f"/api"
    return ScanResponse(
        session_id=session.session_id,
        message=f"Pipeline started for {request.url}",
        stream_url=f"{base_url}/stream/{session.session_id}",
        status_url=f"{base_url}/status/{session.session_id}",
        report_url=f"{base_url}/report/{session.session_id}",
    )


# ---------------------------------------------------------------------------
# GET /api/status/{session_id} — lightweight poll
# ---------------------------------------------------------------------------

@router.get("/status/{session_id}", response_model=SessionStatus)
async def get_status(session_id: str):
    """
    Get the current status of a pipeline session.

    CONCEPT: Polling vs SSE
    Not every client supports SSE (e.g. some mobile environments or proxies
    may buffer or close SSE connections). The status endpoint provides an
    alternative: the client can poll every 2-3 seconds.

    For modern browsers, SSE is preferred. The status endpoint is a fallback.

    CONCEPT: HTTPException
    FastAPI's HTTPException sends a proper HTTP error response with
    a status code and detail message. This is what the client receives
    if they pass a bad session_id.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    return SessionStatus(
        session_id=session.session_id,
        status=session.status,
        current_stage=session.current_stage,
        error=session.error,
        created_at=session.created_at,
    )


# ---------------------------------------------------------------------------
# GET /api/sessions — debug endpoint
# ---------------------------------------------------------------------------

@router.get("/sessions")
async def get_sessions():
    """
    List all active sessions. Useful for debugging.
    In production, this would be behind an admin auth check.
    """
    return {"sessions": list_sessions()}
