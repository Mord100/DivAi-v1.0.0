"""
DivAi — Main LangGraph Orchestration Graph (Phase 2)

WHAT THIS FILE DOES:
  Wires all DivAi agents together into a stateful LangGraph graph.
  This is the orchestration backbone of the entire platform.

CONCEPT: StateGraph — Building a Graph
-----------------------------------------
A StateGraph is the main LangGraph class for building agent pipelines.
You build it by:
  1. Declaring the state type (DivAiState)
  2. Adding nodes (the agent wrapper functions)
  3. Adding edges (fixed connections between nodes)
  4. Adding conditional edges (routing based on state)
  5. Setting the entry point (where execution starts)
  6. Compiling (validates the graph and prepares it to run)

Once compiled, you call app.invoke(initial_state) to run it.
LangGraph handles the loop, state updates, and flow control.

CURRENT GRAPH (Phase 2):
  START -> ingestion -> analysis -> human_review -> END

FUTURE GRAPH (Phase 3+):
  START -> ingestion -> analysis -> human_review
        -> use_case -> human_review -> solution -> proposal -> END
"""

import sys
import os
import json

# Make sure Python can find our modules
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state.divai_state import DivAiState
from graph.nodes import ingestion_node, analysis_node, human_review_node, use_case_node, solution_node, proposal_node


# ---------------------------------------------------------------------------
# Routing function — the Supervisor's decision logic
# ---------------------------------------------------------------------------
# CONCEPT: Conditional Edges (Routing)
# A conditional edge is a function that examines the current state
# and returns the NAME of the next node to go to.
# This is how agents make branching decisions:
#   "If error → go to error_handler"
#   "If analysis done → go to human_review"
#   "If user selected use cases → go to solution agent"
#
# Think of it as a railway switch — the current state determines
# which track the train is sent down next.

def route_after_ingestion(state: DivAiState) -> str:
    """
    After ingestion runs, where do we go?
    - If it failed → end (don't try to analyse bad data)
    - If it succeeded → analysis node
    """
    if state.get("current_stage") == "error":
        print(f"[Supervisor] Ingestion failed. Routing to END.")
        return END
    print(f"[Supervisor] Ingestion OK. Routing to analysis.")
    return "analysis"


def route_after_analysis(state: DivAiState) -> str:
    """
    After analysis runs, where do we go?
    - If it failed → end
    - If it succeeded → human review checkpoint
    """
    if state.get("current_stage") == "error":
        print(f"[Supervisor] Analysis failed. Routing to END.")
        return END
    print(f"[Supervisor] Analysis OK. Routing to human_review.")
    return "human_review"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_graph(use_memory: bool = True):
    """
    Construct and compile the DivAi LangGraph.

    Args:
        use_memory: If True, attach MemorySaver for session persistence.
                    Set False for stateless single-run mode.

    Returns:
        A compiled LangGraph app ready to invoke.

    CONCEPT: Graph Compilation
    .compile() does several things:
      1. Validates that all edge destinations exist as nodes
      2. Checks the state schema for consistency
      3. Attaches the checkpointer (memory) if provided
      4. Returns an optimised runnable object
    After compilation you can't add more nodes — it's like baking a cake.
    """

    # CONCEPT: StateGraph Initialisation
    # We pass DivAiState as the type parameter.
    # LangGraph uses this to:
    #   - Know what fields exist in the state
    #   - Validate that nodes return valid field names
    #   - Apply reducers (like Annotated[list, operator.add])
    graph = StateGraph(DivAiState)

    # --- Add nodes ---
    # Each call registers a named node with its handler function.
    # The string name is what edges reference.
    graph.add_node("ingestion",    ingestion_node)
    graph.add_node("analysis",     analysis_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("use_case",     use_case_node)
    graph.add_node("solution",     solution_node)
    graph.add_node("proposal",     proposal_node)

    # --- Set entry point ---
    # Where does execution begin when we call app.invoke()?
    graph.set_entry_point("ingestion")

    # --- Add conditional edges ---
    # CONCEPT: add_conditional_edges(source, routing_fn, mapping)
    #   source:      the node that just ran
    #   routing_fn:  function that returns a string key
    #   mapping:     maps the string key to the next node name
    #
    # The mapping dict allows routing_fn to return simple strings like
    # "analysis" or "error" rather than actual node references.
    graph.add_conditional_edges(
        "ingestion",
        route_after_ingestion,
        {
            "analysis": "analysis",
            END: END,
        }
    )

    graph.add_conditional_edges(
        "analysis",
        route_after_analysis,
        {
            "human_review": "human_review",
            END: END,
        }
    )

    # --- Human review routes to use_case node ---
    graph.add_edge("human_review", "use_case")

    # --- Use case routes to solution node ---
    graph.add_edge("use_case", "solution")

    # --- Solution routes to proposal ---
    graph.add_edge("solution", "proposal")
    graph.add_edge("proposal", END)

    # --- Compile with optional memory ---
    # CONCEPT: MemorySaver (Checkpointing)
    # MemorySaver stores the full state after every node runs.
    # This means:
    #   - If a node fails, we can resume from the last checkpoint
    #   - Multiple users can have isolated graph sessions (via thread_id)
    #   - We can inspect state at any point in the pipeline
    #
    # In production (Phase 7), we'll swap MemorySaver for a
    # Redis-backed checkpointer so state survives server restarts.
    if use_memory:
        memory = MemorySaver()
        # CONCEPT: interrupt_after — Human-in-the-Loop pause points
        # The graph pauses AFTER these nodes complete.
        # The pipeline runner reads user selections, updates state via
        # app.update_state(), then resumes with app.stream(None, config).
        # Without interrupt_after, the graph runs straight through.
        app = graph.compile(
            checkpointer=memory,
            interrupt_after=["use_case", "solution"],
        )
        print("[Graph] Compiled with MemorySaver + interrupt_after use_case/solution")
    else:
        app = graph.compile()
        print("[Graph] Compiled (no checkpointing)")

    return app


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------

def run_pipeline(url: str, depth: str = "surface", session_id: str = "default") -> dict:
    """
    Run the full DivAi pipeline for a given URL.

    Args:
        url:        Target website URL
        depth:      'surface' | 'deep' | 'both'
        session_id: Unique ID for this user session (scopes the memory)

    Returns:
        The final state dict after the pipeline completes.

    CONCEPT: thread_id — Session Isolation
    When using MemorySaver, each unique thread_id gets its own
    isolated state history. This is how we support multiple users:
      User A's pipeline state is stored under thread_id="user-a-scan-123"
      User B's pipeline state is stored under thread_id="user-b-scan-456"
    They never see each other's data.
    """
    app = build_graph(use_memory=True)

    # Initial state — only the input fields are set
    # All output fields (raw_scrape, intelligence_report, etc.) start as None
    initial_state: DivAiState = {
        "target_url": url,
        "scrape_depth": depth,
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
        "pipeline_log": [],     # Starts empty, each node appends to it
    }

    # CONCEPT: config with thread_id
    # This config is passed to every node invocation.
    # LangGraph uses thread_id to load/save checkpoints for this session.
    config = {"configurable": {"thread_id": session_id}}

    print(f"\n{'='*60}")
    print(f"DivAi Pipeline Starting")
    print(f"URL:       {url}")
    print(f"Depth:     {depth}")
    print(f"Session:   {session_id}")
    print(f"{'='*60}")

    # .invoke() runs the graph to completion (or until an interrupt)
    # Returns the final state
    final_state = app.invoke(initial_state, config=config)

    return final_state


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else "https://stripe.com"
    depth = sys.argv[2] if len(sys.argv) > 2 else "surface"

    final_state = run_pipeline(url, depth, session_id=f"cli-{url[:20]}")

    # Show pipeline audit log
    print(f"\n{'='*60}")
    print("PIPELINE AUDIT LOG")
    print(f"{'='*60}")
    for entry in final_state.get("pipeline_log", []):
        print(f"  [{entry['stage'].upper():15}] {entry['timestamp']} | {entry['message']}")

    # Show error if any
    if final_state.get("error"):
        print(f"\nPIPELINE ERROR: {final_state['error']}")
    else:
        print(f"\nFinal stage: {final_state.get('current_stage')}")

    # Save full state to JSON
    output_path = "output_pipeline_state.json"
    state_to_save = {k: v for k, v in final_state.items()
                     if k != "raw_scrape"}  # Omit raw scrape (large)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(state_to_save, f, indent=2, default=str)
    print(f"Full pipeline state saved to: {output_path}")
