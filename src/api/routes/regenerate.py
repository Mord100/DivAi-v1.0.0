"""
DivAi — Regenerate Proposal Route

POST /api/regenerate/{session_id}
  Re-runs the Proposal Agent with a different selected solution.
  The pipeline has already finished; this replaces only the proposal step.

CONCEPT: Partial Pipeline Re-execution
-----------------------------------------
The full pipeline (Ingestion → Analysis → Use Cases → Solutions → Proposal)
is expensive (~2-4 minutes). But the Proposal Agent only needs two inputs:
  - the selected solution card
  - the intelligence report
Both are already in session.final_state from the original run.

So instead of re-running the whole graph, we call run_proposal_agent()
directly — a targeted one-agent re-run that takes ~15-30 seconds instead
of several minutes.

This is a common pattern in multi-agent systems: cache intermediate results,
allow re-runs at any stage without restarting from scratch.

CONCEPT: run_in_executor for Blocking Work
-------------------------------------------
FastAPI is async — its event loop must never be blocked.
run_proposal_agent() is synchronous (LLM call + docx build, ~15-30s).
asyncio.get_event_loop().run_in_executor(None, fn) offloads it to Python's
default ThreadPoolExecutor, keeping the event loop free to handle other
requests while the proposal generates.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.session_store import get_session

router = APIRouter()


class RegeneratePayload(BaseModel):
    selected_solution_id: str


@router.post("/regenerate/{session_id}")
async def regenerate_proposal(session_id: str, payload: RegeneratePayload):
    """
    Re-run the proposal agent with a different solution card.

    WHAT THIS DOES:
      1. Finds the selected solution in the session's existing solutions list
      2. Runs run_proposal_agent(solution, intelligence_report) in a thread
      3. Replaces proposal_paths in session state with the new result
      4. Uploads the new .docx to Supabase Storage, persists results
      5. Returns the new proposal_paths to the frontend

    Returns 200 with { ok, proposal_paths } on success.
    Returns 404 if session or solution not found.
    Returns 400 if session has no completed pipeline state.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.final_state:
        raise HTTPException(status_code=400, detail="Session has no completed pipeline state")

    solutions = session.final_state.get("solutions") or []
    report = session.final_state.get("intelligence_report") or {}

    solution = next(
        (s for s in solutions if s.get("id") == payload.selected_solution_id),
        None,
    )
    if not solution:
        raise HTTPException(
            status_code=404,
            detail=f"Solution '{payload.selected_solution_id}' not found in this session",
        )

    print(f"\n[Regenerate] Building new proposal for: {solution.get('title')}")

    # Offload the blocking LLM call + docx build to a thread
    loop = asyncio.get_event_loop()

    def _build():
        from agents.document_builder import run_proposal_agent
        return run_proposal_agent(solution, report)

    paths = await loop.run_in_executor(None, _build)

    # Replace proposal_paths in session state
    session.final_state["proposal_paths"] = paths

    # Upload new docx to Supabase Storage and persist updated results
    try:
        from api.supabase_store import upload_proposal, save_scan_results
        docx_path = paths.get("docx")
        if docx_path:
            signed_url = upload_proposal(session_id, docx_path)
            if signed_url:
                session.final_state["proposal_paths"]["signed_url"] = signed_url
                paths["signed_url"] = signed_url
        save_scan_results(session_id, session.final_state)
        print(f"[Regenerate] Persisted to Supabase for session {session_id}")
    except Exception as e:
        print(f"[Regenerate] Supabase persist warning: {e}")

    return {"ok": True, "proposal_paths": paths}
