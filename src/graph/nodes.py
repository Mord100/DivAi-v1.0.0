"""
DivAi Graph Nodes — LangGraph node wrapper functions.

CONCEPT: What is a LangGraph Node?
-------------------------------------
A node is just a Python function with this signature:
    def my_node(state: DivAiState) -> dict:
        ...
        return {"field_to_update": new_value}

Rules:
  1. It receives the FULL current state as input
  2. It returns only the fields it CHANGED (partial update)
  3. LangGraph merges those changes into the state automatically

CONCEPT: Why Wrap Our Agents in Nodes?
-----------------------------------------
Our agents (ingestion_agent.py, analysis_agent.py) are standalone functions.
LangGraph doesn't know about them — it only knows about nodes.
These node wrapper functions are the "adapter" between:
    LangGraph's world (state in, state out)
    Our agent's world  (their own inputs/outputs)

It's the same design pattern used in production systems:
    "Ports and Adapters" (also called Hexagonal Architecture)
The agent is the core logic. The node is the adapter to the framework.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the agents directory to the path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.ingestion_agent import scrape_website
from agents.analysis_agent import run_analysis_agent
from agents.use_case_agent import run_use_case_agent
from agents.solution_agent import run_solution_agent
from agents.document_builder import run_proposal_agent
from state.divai_state import DivAiState


def _log(stage: str, message: str) -> dict:
    """
    Create a pipeline log entry.
    Every node calls this to leave an audit trail in the state.

    CONCEPT: Audit Logging in Agent Pipelines
    An audit log is critical for debugging multi-agent systems.
    When something goes wrong, you need to know:
      - Which agent ran?
      - When?
      - What did it do?
      - Did it succeed or fail?
    We use the pipeline_log field (with Annotated reducer) so every
    node appends its entry without overwriting previous ones.
    """
    return {
        "stage": stage,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Node 1: Ingestion Node
# ---------------------------------------------------------------------------

def ingestion_node(state: DivAiState) -> dict:
    """
    LangGraph node wrapper for the Ingestion Agent.

    Reads from state:  target_url, scrape_depth
    Writes to state:   raw_scrape, current_stage, pipeline_log

    CONCEPT: Sync vs Async in LangGraph Nodes
    Our ingestion agent is async (uses 'await' for Playwright).
    LangGraph nodes are synchronous by default.
    asyncio.run() is the bridge — it runs the async function
    from a synchronous context.
    (LangGraph also supports async nodes with 'async def' — we'll use
    that when we add the FastAPI backend in Phase 6.)
    """
    url = state["target_url"]
    depth = state.get("scrape_depth", "surface")

    print(f"\n[Node: Ingestion] Starting scrape of {url}")

    try:
        # asyncio.run() runs our async scrape_website function synchronously
        raw_scrape = asyncio.run(scrape_website(url, depth))

        print(f"[Node: Ingestion] Complete — "
              f"{len(raw_scrape['dom']['raw_html'])} chars DOM, "
              f"{len(raw_scrape['network_log'])} requests captured")

        return {
            "raw_scrape": raw_scrape,
            "current_stage": "analysis",
            "error": None,
            "pipeline_log": [_log("ingestion", f"Scraped {url} — "
                                               f"{len(raw_scrape['network_log'])} requests captured")],
        }

    except Exception as e:
        error_msg = f"Ingestion failed: {str(e)}"
        print(f"[Node: Ingestion] ERROR — {error_msg}")
        return {
            "current_stage": "error",
            "error": error_msg,
            "pipeline_log": [_log("ingestion", f"FAILED: {error_msg}")],
        }


# ---------------------------------------------------------------------------
# Node 2: Analysis Node
# ---------------------------------------------------------------------------

def analysis_node(state: DivAiState) -> dict:
    """
    LangGraph node wrapper for the Analysis Agent.

    Reads from state:  raw_scrape
    Writes to state:   intelligence_report, current_stage, pipeline_log

    CONCEPT: State Validation in Nodes
    Before running, always check that the required upstream data exists.
    If ingestion_node failed or was skipped, raw_scrape will be None.
    Failing gracefully with a clear error is much better than a cryptic
    AttributeError buried 10 levels deep in a tool call.
    """
    raw_scrape = state.get("raw_scrape")

    if not raw_scrape:
        return {
            "current_stage": "error",
            "error": "Analysis node: raw_scrape is missing. Did ingestion run?",
            "pipeline_log": [_log("analysis", "FAILED: raw_scrape not in state")],
        }

    print(f"\n[Node: Analysis] Analysing {state['target_url']}")

    try:
        # Run the analysis agent — returns an IntelligenceReport Pydantic object
        report = run_analysis_agent(raw_scrape)

        # CONCEPT: Serialising Pydantic Models for State Storage
        # LangGraph state is a dict — it can't store Pydantic objects directly.
        # .model_dump() converts a Pydantic model to a plain dict.
        # This is also why we defined intelligence_report as Optional[dict]
        # rather than Optional[IntelligenceReport] in DivAiState.
        report_dict = report.model_dump()

        print(f"[Node: Analysis] Complete — {report.business_category}")

        return {
            "intelligence_report": report_dict,
            "current_stage": "awaiting_review",   # Signal: human review needed
            "pipeline_log": [_log("analysis", f"Report complete — "
                                              f"{report.business_category}, "
                                              f"{len(report.api_endpoints)} endpoints, "
                                              f"{len(report.key_features)} features")],
        }

    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        print(f"[Node: Analysis] ERROR — {error_msg}")
        return {
            "current_stage": "error",
            "error": error_msg,
            "pipeline_log": [_log("analysis", f"FAILED: {error_msg}")],
        }


# ---------------------------------------------------------------------------
# Node 3: Human Review Node
# ---------------------------------------------------------------------------

def human_review_node(state: DivAiState) -> dict:
    """
    A pass-through node that marks a human review checkpoint.

    CONCEPT: Human-in-the-Loop (HITL)
    In production AI pipelines, you don't always want full automation.
    For DivAi, after Analysis we want to:
      1. Show the user the IntelligenceReport
      2. Let them review, edit, or add context
      3. Then continue to Use Case generation

    LangGraph handles this with 'interrupt_before' — the graph pauses
    at this node and the API returns the current state to the client.
    The user reviews via the frontend, then resumes the graph.

    For now (CLI mode), this node just prints the report summary.
    In Phase 6 (FastAPI), this becomes an actual pause point via the API.

    This node is a "marker" — it doesn't change state, it's a signal
    to LangGraph that human input is needed before proceeding.
    """
    report = state.get("intelligence_report", {})

    print(f"\n{'='*60}")
    print("HUMAN REVIEW CHECKPOINT")
    print(f"{'='*60}")
    print(f"Business Category: {report.get('business_category', 'Unknown')}")
    print(f"Tech Stack:  {report.get('tech_stack', {}).get('frontend_framework', 'Unknown')}")
    print(f"Key Features ({len(report.get('key_features', []))}):")
    for feat in report.get("key_features", [])[:5]:
        print(f"  - {feat}")
    print(f"\nIntelligence report is ready.")
    print(f"In Phase 6 (FastAPI), the graph pauses here for UI review.")
    print(f"{'='*60}\n")

    return {
        "current_stage": "use_case_generation",
        "pipeline_log": [_log("human_review", "Review checkpoint passed")],
    }


# ---------------------------------------------------------------------------
# Node 4: Use Case Node
# ---------------------------------------------------------------------------

def use_case_node(state: DivAiState) -> dict:
    """
    LangGraph node wrapper for the Use Case Agent.

    Reads from state:  intelligence_report
    Writes to state:   use_cases, current_stage, pipeline_log

    CONCEPT: Passing Pydantic Output Through State
    The Use Case Agent returns a UseCaseList Pydantic object.
    We convert it to a plain list of dicts with .model_dump() so it
    can be serialised in the state dict (LangGraph state is JSON-serialisable).
    """
    report = state.get("intelligence_report")

    if not report:
        return {
            "current_stage": "error",
            "error": "Use case node: intelligence_report missing.",
            "pipeline_log": [_log("use_case", "FAILED: intelligence_report not in state")],
        }

    print(f"\n[Node: UseCase] Generating use cases...")

    try:
        result = run_use_case_agent(report)

        # Convert Pydantic objects to plain dicts for state storage
        use_cases_dicts = [uc.model_dump() for uc in result.use_cases]

        print(f"[Node: UseCase] {len(use_cases_dicts)} use cases generated")

        return {
            "use_cases": use_cases_dicts,
            "current_stage": "awaiting_use_case_selection",
            "pipeline_log": [_log("use_case",
                f"{len(use_cases_dicts)} use cases generated. "
                f"Top: {use_cases_dicts[0]['title'] if use_cases_dicts else 'none'}"
            )],
        }

    except Exception as e:
        error_msg = f"Use case generation failed: {str(e)}"
        print(f"[Node: UseCase] ERROR — {error_msg}")
        return {
            "current_stage": "error",
            "error": error_msg,
            "pipeline_log": [_log("use_case", f"FAILED: {error_msg}")],
        }


# ---------------------------------------------------------------------------
# Node 5: Solution Node
# ---------------------------------------------------------------------------

def solution_node(state: DivAiState) -> dict:
    """
    LangGraph node wrapper for the Solution Agent.

    Reads from state:  use_cases, selected_use_case_ids
    Writes to state:   solutions, current_stage, pipeline_log

    CONCEPT: Optional State Fields Drive Agent Behaviour
    selected_use_case_ids may be None (user hasn't selected yet in CLI mode).
    The Solution Agent handles this gracefully with a sensible default
    (auto-select top 2). In production, the frontend populates this field
    before resuming the graph after the human review pause.
    """
    use_cases = state.get("use_cases")
    selected_ids = state.get("selected_use_case_ids")

    if not use_cases:
        return {
            "current_stage": "error",
            "error": "Solution node: use_cases missing.",
            "pipeline_log": [_log("solution", "FAILED: use_cases not in state")],
        }

    print(f"\n[Node: Solution] Generating solution cards...")

    try:
        result = run_solution_agent(use_cases, selected_ids)
        solutions_dicts = [sol.model_dump() for sol in result.solutions]

        print(f"[Node: Solution] {len(solutions_dicts)} solution cards ready")

        return {
            "solutions": solutions_dicts,
            "current_stage": "awaiting_solution_selection",
            "pipeline_log": [_log("solution",
                f"{len(solutions_dicts)} solutions generated. "
                f"Recommendation: {result.recommendation[:80]}..."
            )],
        }

    except Exception as e:
        error_msg = f"Solution generation failed: {str(e)}"
        print(f"[Node: Solution] ERROR — {error_msg}")
        return {
            "current_stage": "error",
            "error": error_msg,
            "pipeline_log": [_log("solution", f"FAILED: {error_msg}")],
        }


# ---------------------------------------------------------------------------
# Node 6: Proposal Node
# ---------------------------------------------------------------------------

def proposal_node(state: DivAiState) -> dict:
    """
    LangGraph node wrapper for the Proposal Agent + Document Builder.

    Reads from state:  solutions, selected_solution_id, intelligence_report
    Writes to state:   proposal_paths, current_stage, pipeline_log

    CONCEPT: Auto-selecting a Solution in CLI Mode
    In production the user picks a solution from the frontend.
    In CLI mode we auto-select the first (highest-scored) solution.
    The selected_solution_id field tells us which one — None = auto-select.
    """
    solutions = state.get("solutions", [])
    selected_id = state.get("selected_solution_id")
    report = state.get("intelligence_report", {})

    if not solutions:
        return {
            "current_stage": "error",
            "error": "Proposal node: no solutions in state.",
            "pipeline_log": [_log("proposal", "FAILED: solutions not in state")],
        }

    # Pick the selected solution (or default to first)
    solution = next(
        (s for s in solutions if s.get("id") == selected_id),
        solutions[0]
    )

    print(f"\n[Node: Proposal] Generating proposal for: {solution.get('title')}")

    try:
        paths = run_proposal_agent(solution, report)

        print(f"[Node: Proposal] Document saved: {paths['docx']}")

        return {
            "proposal_paths": paths,
            "current_stage": "complete",
            "pipeline_log": [_log("proposal",
                f"Proposal generated: '{paths['title']}' → {paths['docx']}"
            )],
        }

    except Exception as e:
        error_msg = f"Proposal generation failed: {str(e)}"
        print(f"[Node: Proposal] ERROR — {error_msg}")
        return {
            "current_stage": "error",
            "error": error_msg,
            "pipeline_log": [_log("proposal", f"FAILED: {error_msg}")],
        }
