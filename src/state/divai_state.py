"""
DivAi Shared State — the single source of truth passed through every LangGraph node.

CONCEPT: Why TypedDict for State?
----------------------------------
LangGraph requires state to be a TypedDict (or dataclass).
A TypedDict is a Python dict where each key has a declared type.
LangGraph reads these type annotations to understand:
  - What fields exist
  - How to merge state updates from different nodes
  - What the "shape" of state looks like at compile time

CONCEPT: The Annotated Reducer Pattern
----------------------------------------
LangGraph nodes return PARTIAL state — only the fields they changed.
When two nodes both update the same field, LangGraph needs to know HOW to merge them.
The Annotated[list, operator.add] syntax says:
  "When merging 'messages', use operator.add (i.e. append, don't overwrite)"
Without this, the second node's messages would REPLACE the first node's messages.

Think of it like a shared Google Doc:
  - Without reducer: you overwrite someone else's text
  - With reducer:    your text gets appended after theirs
"""

import operator
from typing import Annotated, Optional, TypedDict
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic models — typed shapes for each agent's structured output
# ---------------------------------------------------------------------------

class TechStack(BaseModel):
    frontend_framework: str
    language: str
    hosting_signals: list[str]
    database_signals: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class DetectedEndpoint(BaseModel):
    method: str
    url_pattern: str
    inferred_purpose: str
    data_signals: list[str]


class AuthPattern(BaseModel):
    method: str
    providers: list[str]
    token_refresh: bool
    notes: str


class IntelligenceReport(BaseModel):
    """Structured output of the Analysis Agent."""
    target_url: str
    tech_stack: TechStack
    api_endpoints: list[DetectedEndpoint]
    auth_pattern: AuthPattern
    ui_patterns: list[str]
    integrations: list[str]
    data_models: list[str]
    business_category: str
    key_features: list[str]
    analyst_notes: str


class UseCase(BaseModel):
    id: str
    title: str
    description: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    supporting_evidence: list[str]
    tags: list[str]
    effort_estimate: str    # 'Low' | 'Medium' | 'High'


class Solution(BaseModel):
    id: str
    title: str
    pitch: str
    stack: list[str]
    timeline: str
    value_score: str        # 'Low' | 'High' | 'Very High'
    effort_score: str
    architecture_overview: str
    risks: list[str]


# ---------------------------------------------------------------------------
# DivAiState — the shared conveyor belt for the entire pipeline
# ---------------------------------------------------------------------------
# CONCEPT: Optional fields
# Most fields start as None because agents fill them in progressively.
# The pipeline starts with only target_url set.
# After the Ingestion Agent: raw_dom and network_log are filled.
# After the Analysis Agent: intelligence_report is filled.
# And so on...
#
# CONCEPT: Annotated[list, operator.add]
# This is the "reducer" pattern. operator.add on a list = append.
# So every agent can ADD to pipeline_log without overwriting it.
# This gives us a full audit trail of the pipeline's progress.

class DivAiState(TypedDict):

    # --- INPUT (set before the graph starts) ---
    target_url: str                           # The website to analyse
    scrape_depth: str                         # 'surface' | 'deep' | 'both'
    client_context: Optional[str]             # Optional brief from the client

    # --- INGESTION AGENT output ---
    raw_scrape: Optional[dict]                # Full result from ingestion_agent.py

    # --- ANALYSIS AGENT output ---
    intelligence_report: Optional[dict]       # Serialised IntelligenceReport

    # --- USE CASE AGENT output (Phase 3) ---
    use_cases: Optional[list]                 # List of UseCase dicts
    selected_use_case_ids: Optional[list]     # User selects which to pursue

    # --- SOLUTION AGENT output (Phase 3) ---
    solutions: Optional[list]                 # List of Solution dicts
    selected_solution_id: Optional[str]       # User selects final solution

    # --- PROPOSAL AGENT output (Phase 5) ---
    proposal_paths: Optional[dict]            # {docx: path, pdf: path, notion: url}

    # --- CONTROL (managed by Supervisor) ---
    current_stage: str                        # Which stage we're in
    error: Optional[str]                      # Error message if something fails

    # --- AUDIT LOG — appended to by every node, never overwritten ---
    # operator.add on a list = append new entries to existing entries
    pipeline_log: Annotated[list, operator.add]
