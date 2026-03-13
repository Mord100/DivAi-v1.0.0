"""
DivAi — API Request/Response Models (Phase 6)

WHAT THIS FILE DOES:
  Defines the Pydantic models for every API endpoint.
  FastAPI uses these for automatic request validation AND
  automatic OpenAPI documentation generation.

CONCEPT: FastAPI + Pydantic Integration
-----------------------------------------
FastAPI reads your Pydantic models and does three things automatically:
  1. Validates incoming request data (returns 422 if invalid)
  2. Serialises outgoing response data to JSON
  3. Generates the /docs Swagger UI so you can test the API in a browser

You already know Pydantic from the agents (IntelligenceReport, SolutionCard etc.).
Here we use the same pattern for HTTP request/response shapes.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ---------------------------------------------------------------------------
# Request models — what the client sends TO the server
# ---------------------------------------------------------------------------

class ScanRequest(BaseModel):
    """
    POST /api/scan — request body.

    CONCEPT: Request Body vs Query Params vs Path Params
    FastAPI routes can receive data three ways:
      /api/scan/{session_id}    ← path parameter   (part of the URL)
      /api/scan?depth=deep      ← query parameter  (after the ?)
      POST body: {"url": ...}   ← request body     (JSON body for POST/PUT)

    Pydantic models map to request bodies — FastAPI knows it's JSON.
    """
    url: str = Field(
        description="Target website URL to analyze",
        examples=["https://stripe.com"]
    )
    depth: str = Field(
        default="surface",
        description="Scrape depth: 'surface' (fast) or 'deep' (thorough)"
    )


# ---------------------------------------------------------------------------
# Response models — what the server sends BACK to the client
# ---------------------------------------------------------------------------

class ScanResponse(BaseModel):
    """
    POST /api/scan — response.
    Returns the session_id the client uses to connect to the SSE stream.
    """
    session_id: str
    message: str
    stream_url: str     # URL to connect to SSE stream
    status_url: str     # URL to poll status
    report_url: str     # URL to get final report when done


class SessionStatus(BaseModel):
    """
    GET /api/status/{session_id} — lightweight status check.
    The client can poll this to know when the pipeline is done.
    """
    session_id: str
    status: str           # "pending" | "running" | "complete" | "error"
    current_stage: Optional[str] = None
    error: Optional[str] = None
    created_at: str


class PipelineEvent(BaseModel):
    """
    SSE event payload — one event per LangGraph node completion.

    CONCEPT: Why Sanitise SSE Events?
    The pipeline state includes raw_scrape (up to 700KB of HTML).
    We never send that over SSE — it would flood the client connection.
    Instead we send a compact summary: counts, titles, key metrics.

    type values:
      "pipeline_start"    — pipeline just kicked off
      "node_complete"     — a LangGraph node finished
      "pipeline_complete" — all nodes done, report ready
      "error"             — something failed
      "heartbeat"         — keep-alive ping (every 25s if idle)
    """
    type: str
    node: Optional[str] = None        # which node just ran
    stage: Optional[str] = None       # current_stage from state
    data: Optional[dict] = None       # sanitised node output
    message: Optional[str] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )


class ReportResponse(BaseModel):
    """
    GET /api/report/{session_id} — full pipeline result.
    Returned when status == "complete".

    CONCEPT: Why a Separate Report Endpoint?
    The SSE stream only sends compact summaries to keep the connection fast.
    The full report (intelligence_report, use_cases, solutions, proposal_paths)
    is served separately on demand — the client fetches it once, when done.
    This is the "fetch-on-demand" pattern common in streaming UIs.
    """
    session_id: str
    status: str
    intelligence_report: Optional[dict] = None
    use_cases: Optional[list] = None
    solutions: Optional[list] = None
    proposal_paths: Optional[dict] = None
    pipeline_log: Optional[list] = None
    error: Optional[str] = None
