"""
DivAi — Rerun Solutions Route

POST /api/rerun-solutions/{session_id}
  Re-runs the Solution Agent with a new set of selected use case IDs.

CONCEPT: Stateless Generation
--------------------------------
The frontend passes the full use_cases list directly in the request body
so the endpoint doesn't depend on in-memory session state (which is lost
on server restart). Only session_id is needed for Supabase persistence.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class RerunSolutionsPayload(BaseModel):
    selected_use_case_ids: list[str]
    use_cases: list[dict]   # full use_cases list from the frontend


@router.post("/rerun-solutions/{session_id}")
async def rerun_solutions(session_id: str, payload: RerunSolutionsPayload):
    """
    Re-run the Solution Agent with a new use case selection.

    Accepts use_cases directly — no in-memory session lookup needed.
    Only uses session_id for Supabase persistence.
    """
    if not payload.use_cases:
        raise HTTPException(status_code=422, detail="use_cases is required")
    if not payload.selected_use_case_ids:
        raise HTTPException(status_code=422, detail="At least one use case ID must be selected")

    print(f"\n[Rerun Solutions] session={session_id}, selected={payload.selected_use_case_ids}")

    loop = asyncio.get_running_loop()

    def _build():
        from agents.solution_agent import run_solution_agent
        result = run_solution_agent(payload.use_cases, payload.selected_use_case_ids)
        return [s.model_dump() for s in result.solutions]

    new_solutions = await loop.run_in_executor(None, _build)

    # Persist to Supabase (update just the solutions column)
    try:
        from api.supabase_store import get_client
        get_client().table("scan_results").update(
            {"solutions": new_solutions}
        ).eq("id", session_id).execute()
        print(f"[Rerun Solutions] Persisted {len(new_solutions)} solutions for session {session_id}")
    except Exception as e:
        print(f"[Rerun Solutions] Supabase persist warning: {e}")

    # Also update in-memory session if alive
    try:
        from api.session_store import get_session
        session = get_session(session_id)
        if session and session.final_state:
            session.final_state["solutions"] = new_solutions
    except Exception:
        pass

    return {"ok": True, "solutions": new_solutions}
