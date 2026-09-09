"""
DivAi — Regenerate Proposal Route

POST /api/regenerate/{session_id}
  Re-runs the Proposal Agent with a different selected solution.

CONCEPT: Stateless Generation
--------------------------------
Rather than reading solution and intelligence_report from the in-memory
session store (which is lost on server restart), the frontend passes them
directly in the request body. The frontend already has all this data from
the report it loaded.

This makes the endpoint stateless for the computation step — it only uses
session_id to upload the .docx to Supabase Storage and update the DB row.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class RegeneratePayload(BaseModel):
    solution: dict           # full SolutionCard dict from the frontend
    intelligence_report: dict  # full intelligence report from the frontend


@router.post("/regenerate/{session_id}")
async def regenerate_proposal(session_id: str, payload: RegeneratePayload):
    """
    Re-run the proposal agent with a different solution card.

    Accepts the solution and intelligence_report directly — no in-memory
    session lookup needed. Only uses session_id for Supabase persistence.
    """
    solution = payload.solution
    report = payload.intelligence_report

    if not solution:
        raise HTTPException(status_code=422, detail="solution is required")
    if not report:
        raise HTTPException(status_code=422, detail="intelligence_report is required")

    print(f"\n[Regenerate] Building proposal for: {solution.get('title')} (session={session_id})")

    loop = asyncio.get_running_loop()

    def _build():
        from agents.document_builder import run_proposal_agent
        return run_proposal_agent(solution, report)

    paths = await loop.run_in_executor(None, _build)

    # Persist to Supabase (update just the proposal_paths column)
    try:
        from api.supabase_store import get_client, upload_proposal
        docx_path = paths.get("docx")
        if docx_path:
            signed_url = upload_proposal(session_id, docx_path)
            if signed_url:
                paths["signed_url"] = signed_url
        get_client().table("scan_results").update(
            {"proposal_paths": paths}
        ).eq("id", session_id).execute()
        print(f"[Regenerate] Persisted to Supabase for session {session_id}")
    except Exception as e:
        print(f"[Regenerate] Supabase persist warning: {e}")

    # Also update in-memory session if it happens to be alive
    try:
        from api.session_store import get_session
        session = get_session(session_id)
        if session and session.final_state:
            session.final_state["proposal_paths"] = paths
    except Exception:
        pass

    return {"ok": True, "proposal_paths": paths}
