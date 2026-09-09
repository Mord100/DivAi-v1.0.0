"""
DivAi — Rerun Solutions Route

POST /api/rerun-solutions/{session_id}
  Re-runs the Solution Agent with a new set of selected use case IDs.
  The pipeline's intelligence + use_cases are already in session state —
  only the Solution Agent (and nothing upstream) needs to re-run.

CONCEPT: Partial Re-execution at Any Stage
-------------------------------------------
Because every agent writes its output to session.final_state, we can
re-enter the pipeline at any node without repeating the expensive work
that came before it.

  Ingestion   (~30s)  already done — raw_dom in final_state
  Analysis    (~20s)  already done — intelligence_report in final_state
  Use Cases   (~15s)  already done — use_cases in final_state
  Solutions   (~10s)  ← re-run THIS with a different use case selection
  Proposal    (~15s)  user picks a solution from the new list and re-runs separately

This gives the user full control to explore different paths through
the solution space without paying the full pipeline cost each time.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.session_store import get_session

router = APIRouter()


class RerunSolutionsPayload(BaseModel):
    selected_use_case_ids: list[str]


@router.post("/rerun-solutions/{session_id}")
async def rerun_solutions(session_id: str, payload: RerunSolutionsPayload):
    """
    Re-run the Solution Agent with a new use case selection.

    WHAT THIS DOES:
      1. Pulls the existing use_cases list from session.final_state
      2. Filters to only the selected IDs (same logic as the original pipeline)
      3. Runs run_solution_agent() in a thread (~10-15s)
      4. Updates session.final_state["solutions"] with the new cards
      5. Persists to Supabase
      6. Returns { ok, solutions } — the frontend switches to the Solutions tab

    The user then picks a solution card and hits "Generate proposal",
    which calls POST /api/regenerate/{session_id}.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.final_state:
        raise HTTPException(status_code=400, detail="Session has no completed pipeline state")

    use_cases = session.final_state.get("use_cases") or []
    if not use_cases:
        raise HTTPException(status_code=400, detail="No use cases in session state")

    if not payload.selected_use_case_ids:
        raise HTTPException(status_code=422, detail="At least one use case ID must be selected")

    print(f"\n[Rerun Solutions] session={session_id}, selected={payload.selected_use_case_ids}")

    loop = asyncio.get_event_loop()

    def _build():
        from agents.solution_agent import run_solution_agent
        result = run_solution_agent(use_cases, payload.selected_use_case_ids)
        return [s.model_dump() for s in result.solutions]

    new_solutions = await loop.run_in_executor(None, _build)

    # Replace solutions in session state
    session.final_state["solutions"] = new_solutions

    # Persist updated state to Supabase
    try:
        from api.supabase_store import save_scan_results
        save_scan_results(session_id, session.final_state)
        print(f"[Rerun Solutions] Persisted {len(new_solutions)} new solutions for session {session_id}")
    except Exception as e:
        print(f"[Rerun Solutions] Supabase persist warning: {e}")

    return {"ok": True, "solutions": new_solutions}
