"""
DivAi — Report Route (Phase 6)

ENDPOINT:
  GET /api/report/{session_id}

CONCEPT: Fetch-on-Demand Pattern
----------------------------------
The SSE stream sends compact summaries (node labels, counts, titles).
It deliberately omits large nested structures like the full
intelligence_report and all use case + solution details.

When the pipeline completes, the frontend fetches the full data
with a single GET /api/report/{session_id} call.

This is the "fetch-on-demand" pattern:
  1. Stream: fast, small, real-time progress
  2. Report: one fetch, full data, on completion

Contrast this with alternatives:
  - Send everything over SSE → slow, wastes bandwidth for users who leave early
  - Polling /report every 2s → hammers the server, no real-time feel
  The combined SSE + fetch-on-demand gives best of both worlds.
"""

import sys
import os

from fastapi import APIRouter, HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from api.models import ReportResponse
from api.session_store import get_session

router = APIRouter()


@router.get("/report/{session_id}", response_model=ReportResponse)
async def get_report(session_id: str):
    """
    Return the full pipeline result for a completed session.

    CONCEPT: HTTP Status Codes
    202 Accepted  — request understood, but result not ready yet
    200 OK        — result is ready, here it is
    404 Not Found — no such session

    Returning 202 instead of 200 when still running tells the client:
    "I understand what you want, but come back later." This is more
    semantically correct than returning an empty 200.
    """
    session = get_session(session_id)

    # ── In-memory session found ──────────────────────────────────────────────
    if session:
        if session.status in ("pending", "running"):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=202,
                content={
                    "session_id": session_id,
                    "status": session.status,
                    "message": "Pipeline is still running. Check back when status is 'complete'.",
                }
            )
        if session.status == "error":
            return ReportResponse(session_id=session_id, status="error", error=session.error)

        final = session.final_state or {}
        return ReportResponse(
            session_id=session_id,
            status="complete",
            intelligence_report=final.get("intelligence_report"),
            use_cases=final.get("use_cases"),
            solutions=final.get("solutions"),
            proposal_paths=final.get("proposal_paths"),
            pipeline_log=final.get("pipeline_log"),
        )

    # ── Session not in memory — fall back to Supabase (server restarted) ────
    from api.supabase_store import load_scan_from_supabase
    data = load_scan_from_supabase(session_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    status = data.get("status", "unknown")
    if status in ("pending", "running"):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=202,
            content={"session_id": session_id, "status": status,
                     "message": "Pipeline is still running."},
        )
    if status == "error":
        return ReportResponse(session_id=session_id, status="error", error="Pipeline failed")

    return ReportResponse(
        session_id=session_id,
        status="complete",
        intelligence_report=data.get("intelligence_report"),
        use_cases=data.get("use_cases"),
        solutions=data.get("solutions"),
        proposal_paths=data.get("proposal_paths"),
        pipeline_log=data.get("pipeline_log"),
    )
