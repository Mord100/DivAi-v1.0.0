"""
DivAi — Interact Route

POST /api/interact/{session_id}
  Receives user selections from the frontend and unblocks the pipeline thread.

GET  /api/interact/{session_id}
  Returns the current pending interaction so the frontend can render the right UI.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from api.session_store import get_session

router = APIRouter()


class InteractionPayload(BaseModel):
    selected_use_case_ids: Optional[list[str]] = None
    selected_solution_id: Optional[str] = None


@router.get("/interact/{session_id}")
async def get_pending_interaction(session_id: str):
    """Return what interaction is currently expected from the user."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "status": session.status,
        "pending_interaction": session.pending_interaction,
    }


@router.post("/interact/{session_id}")
async def submit_interaction(session_id: str, payload: InteractionPayload):
    """
    Accept user selections and resume the pipeline.

    CONCEPT: Unblocking a Thread from Async Code
    ----------------------------------------------
    The pipeline thread is blocked on session.interaction_event.wait().
    This is a threading.Event — safe to call .set() from any thread or coroutine.
    Calling .set() here (from the FastAPI async handler) immediately
    unblocks the pipeline thread so it can continue.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "awaiting_input":
        raise HTTPException(
            status_code=409,
            detail=f"Session is not awaiting input (status: {session.status})"
        )

    # Store the user's choices
    session.interaction_response = payload.model_dump(exclude_none=True)

    # Unblock the pipeline thread
    session.interaction_event.set()

    return {"ok": True, "message": "Pipeline resumed"}
