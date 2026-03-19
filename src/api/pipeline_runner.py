"""
DivAi — Pipeline Runner with Human-in-the-Loop (Phase 6 updated)

CONCEPT: LangGraph interrupt_after — How Pause/Resume Works
-------------------------------------------------------------
When the graph is compiled with interrupt_after=["use_case", "solution"],
it pauses AFTER those nodes complete. The stream() generator ends early.

To detect a pause: app.get_state(config).next  →  ("solution",) or ("proposal",)
  If .next is empty → graph finished normally (END reached)
  If .next is non-empty → graph is paused, waiting to be resumed

To inject user input: app.update_state(config, {"field": value})
  This writes directly into the checkpointed state.

To resume: app.stream(None, config=config, stream_mode="updates")
  Passing None as input tells LangGraph "load state from checkpoint, don't reinitialise"

The full flow:
  stream(initial_state) → runs ingestion → analysis → human_review → use_case → PAUSE
  emit interaction_required event → wait for user → app.update_state(selected_use_case_ids)
  stream(None) → runs solution → PAUSE
  emit interaction_required event → wait for user → app.update_state(selected_solution_id)
  stream(None) → runs proposal → END
"""

import sys
import os
import traceback
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.session_store import PipelineSession

INTERACTION_TIMEOUT = 600   # 10 minutes for user to respond

NODE_LABELS = {
    "ingestion":    "Scraping website",
    "analysis":     "Analysing business signals",
    "human_review": "Intelligence report ready",
    "use_case":     "Generating use cases",
    "solution":     "Designing solutions",
    "proposal":     "Writing proposal",
}


# ---------------------------------------------------------------------------
# Sanitise node output — strip blobs before sending over SSEeee
# ---------------------------------------------------------------------------

def _sanitise_node_output(node_name: str, updates: dict) -> dict:
    safe: dict = {
        "current_stage": updates.get("current_stage"),
        "error": updates.get("error"),
    }

    if node_name == "ingestion":
        scrape = updates.get("raw_scrape") or {}
        dom = scrape.get("dom") or {}
        safe["scrape_summary"] = {
            "url": scrape.get("target_url"),
            "dom_chars": len(dom.get("raw_html", "")),
            "request_count": len(scrape.get("network_log", [])),
            "tech_detected": list((scrape.get("tech_signals") or {}).get("frameworks", [])),
        }

    elif node_name == "analysis":
        report = updates.get("intelligence_report") or {}
        safe["report_summary"] = {
            "business_category": report.get("business_category"),
            "key_features_count": len(report.get("key_features", [])),
            "endpoints_count": len(report.get("api_endpoints", [])),
            "tech_stack": report.get("tech_stack", {}),
            "key_features": report.get("key_features", [])[:8],
            "integrations": report.get("integrations", []),
            "analyst_notes": report.get("analyst_notes", ""),
        }

    elif node_name == "human_review":
        safe["review_note"] = "Intelligence report ready for review"

    elif node_name == "use_case":
        use_cases = updates.get("use_cases") or []
        safe["use_cases_count"] = len(use_cases)
        safe["use_case_titles"] = [
            {"title": uc.get("title"), "confidence": uc.get("confidence_score")}
            for uc in use_cases[:5]
        ]

    elif node_name == "solution":
        solutions = updates.get("solutions") or []
        safe["solutions_count"] = len(solutions)
        safe["solution_titles"] = [
            {"title": s.get("title"), "timeline": s.get("timeline")}
            for s in solutions
        ]

    elif node_name == "proposal":
        paths = updates.get("proposal_paths") or {}
        safe["proposal"] = {
            "title": paths.get("title"),
            "client": paths.get("client"),
            "docx_path": paths.get("docx"),
        }

    return safe


# ---------------------------------------------------------------------------
# Per-chunk processing helper
# ---------------------------------------------------------------------------

def _process_chunk(session: PipelineSession, chunk: dict) -> bool:
    """
    Emit one SSE event per node in the chunk.
    Returns True if an error node was detected (caller should abort).

    LangGraph emits special interrupt marker chunks like:
        {"__interrupt__": (Interrupt(...),)}
    where the value is a tuple, not a state dict. We skip those —
    the caller uses app.get_state() to detect the pause instead.
    """
    for node_name, node_updates in chunk.items():
        # Skip LangGraph internal markers (interrupt signals, etc.)
        if not isinstance(node_updates, dict):
            continue

        label = NODE_LABELS.get(node_name, node_name)
        sanitised = _sanitise_node_output(node_name, node_updates)
        session.current_stage = node_updates.get("current_stage")

        session.emit({
            "type": "node_complete",
            "node": node_name,
            "label": label,
            "stage": node_updates.get("current_stage"),
            "data": sanitised,
            "timestamp": datetime.now().isoformat(),
        })

        if node_updates.get("current_stage") == "error":
            error_msg = node_updates.get("error", "Unknown error")
            session.status = "error"
            session.error = error_msg
            session.emit({
                "type": "error",
                "message": error_msg,
                "node": node_name,
                "timestamp": datetime.now().isoformat(),
            })
            return True

    return False


def _finalize(session: PipelineSession, app, config: dict) -> None:
    """Store final state, emit pipeline_complete, close stream."""
    snapshot = app.get_state(config)
    full_state = dict(snapshot.values)
    session.final_state = {k: v for k, v in full_state.items() if k != "raw_scrape"}
    session.status = "complete"
    session.current_stage = "complete"

    session.emit({
        "type": "pipeline_complete",
        "message": "Pipeline complete. Report is ready.",
        "proposal_title": (session.final_state.get("proposal_paths") or {}).get("title"),
        "timestamp": datetime.now().isoformat(),
    })
    session.emit({"type": "stream_end", "timestamp": datetime.now().isoformat()})


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_pipeline_in_thread(session: PipelineSession) -> None:
    """
    Run the DivAi pipeline in stages, pausing for user input.

    Stage 1: ingestion → analysis → human_review → use_case [PAUSE]
    Stage 2: solution [PAUSE]
    Stage 3: proposal [DONE]
    """
    from graph.divai_graph import build_graph

    session.status = "running"
    session.emit({
        "type": "pipeline_start",
        "message": f"Starting pipeline for {session.url}",
        "url": session.url,
        "depth": session.depth,
        "timestamp": datetime.now().isoformat(),
    })

    try:
        app = build_graph(use_memory=True)
        config = {"configurable": {"thread_id": session.session_id}}

        initial_state = {
            "target_url": session.url,
            "scrape_depth": session.depth,
            "client_context": None,
            "raw_scrape": None,
            "intelligence_report": None,
            "use_cases": None,
            "selected_use_case_ids": None,
            "solutions": None,
            "selected_solution_id": None,
            "proposal_paths": None,
            "current_stage": "ingestion",
            "error": None,
            "pipeline_log": [],
        }

        # ── Stage 1: ingestion → analysis → human_review → use_case ──────
        for chunk in app.stream(initial_state, config=config, stream_mode="updates"):
            if _process_chunk(session, chunk):
                return

        state = app.get_state(config)

        # Check if graph ended early (error routing sent us to END)
        if not state.next:
            _finalize(session, app, config)
            return

        # ── Pause 1: use_case completed, need use case selection ──────────
        use_cases = state.values.get("use_cases") or []
        session.status = "awaiting_input"
        session.pending_interaction = {
            "type": "select_use_cases",
            "use_cases": use_cases,
        }
        session.emit({
            "type": "interaction_required",
            "interaction_type": "select_use_cases",
            "data": {
                "use_cases": use_cases,
                "message": "Select which use cases to build solutions for.",
            },
            "timestamp": datetime.now().isoformat(),
        })

        # Block this thread until the interact endpoint sets the event
        timed_out = not session.interaction_event.wait(timeout=INTERACTION_TIMEOUT)
        session.interaction_event.clear()
        session.status = "running"
        session.pending_interaction = None

        selected_ids = None
        if not timed_out and session.interaction_response:
            selected_ids = session.interaction_response.get("selected_use_case_ids")

        # Default: top 2 use cases if user didn't respond or selected none
        if not selected_ids and use_cases:
            selected_ids = [uc.get("id") for uc in use_cases[:2]]

        app.update_state(config, {"selected_use_case_ids": selected_ids})

        # ── Stage 2: solution ─────────────────────────────────────────────
        for chunk in app.stream(None, config=config, stream_mode="updates"):
            if _process_chunk(session, chunk):
                return

        state = app.get_state(config)
        if not state.next:
            _finalize(session, app, config)
            return

        # ── Pause 2: solution completed, need solution selection ──────────
        solutions = state.values.get("solutions") or []
        session.status = "awaiting_input"
        session.pending_interaction = {
            "type": "select_solution",
            "solutions": solutions,
        }
        session.emit({
            "type": "interaction_required",
            "interaction_type": "select_solution",
            "data": {
                "solutions": solutions,
                "message": "Select the solution to build.",
            },
            "timestamp": datetime.now().isoformat(),
        })

        timed_out = not session.interaction_event.wait(timeout=INTERACTION_TIMEOUT)
        session.interaction_event.clear()
        session.status = "running"
        session.pending_interaction = None

        selected_id = None
        if not timed_out and session.interaction_response:
            selected_id = session.interaction_response.get("selected_solution_id")

        if not selected_id and solutions:
            selected_id = solutions[0].get("id")

        app.update_state(config, {"selected_solution_id": selected_id})

        # ── Stage 3: proposal ─────────────────────────────────────────────
        for chunk in app.stream(None, config=config, stream_mode="updates"):
            if _process_chunk(session, chunk):
                return

        _finalize(session, app, config)

    except Exception as e:
        tb = traceback.format_exc()
        error_msg = f"Pipeline crashed: {str(e)}"
        print(f"[Pipeline] ERROR:\n{tb}")
        session.status = "error"
        session.error = error_msg
        session.emit({
            "type": "error",
            "message": error_msg,
            "timestamp": datetime.now().isoformat(),
        })
        session.emit({"type": "stream_end", "timestamp": datetime.now().isoformat()})
