"""
DivAi — Solution Agent (Phase 3)

WHAT THIS AGENT DOES:
  Takes selected use cases and matches them to concrete technical
  solutions from the agency's blueprint library using RAG + Claude.

WHERE IT FITS IN DIVAI:
  Layer 3 — Solution Layer
  Fourth node in the LangGraph pipeline.
  Reads:  use_cases + selected_use_case_ids (from state)
  Writes: solutions

CONCEPT: Pattern Recognition — Same Structure, Different Domain
-----------------------------------------------------------------
Compare this file to use_case_agent.py:
  - Same LCEL chain pattern (retriever → prompt | llm.with_structured_output)
  - Same RAG approach (query → retrieve → inject context)
  - Different schema (Solution vs UseCase)
  - Different prompt (architecture focus vs opportunity focus)
  - Different KB (solution_blueprint_kb vs use_case_kb)

This is the core skill of AI engineering: learn a pattern once,
apply it across many problems. The pattern is:
    RAG context + structured prompt + structured output = reliable agent
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from rag.solution_knowledge_base import get_solution_retriever

load_dotenv()


# ---------------------------------------------------------------------------
# Output Schema
# ---------------------------------------------------------------------------

class SolutionCard(BaseModel):
    """A concrete technical solution for a selected use case."""
    id: str = Field(description="Unique ID e.g. 'sol_001'")
    title: str = Field(description="Solution name e.g. 'AI Support Agent (RAG-Powered)'")
    pitch: str = Field(description="One compelling sentence selling this solution")
    architecture_overview: str = Field(
        description="2-3 sentence description of the system architecture"
    )
    stack: list[str] = Field(description="Key technologies e.g. ['Python', 'FastAPI', 'Claude API']")
    phases: list[str] = Field(description="Delivery phases with week numbers")
    timeline: str = Field(description="Total duration e.g. '6 weeks'")
    effort_score: str = Field(description="'Low' | 'Medium' | 'High'")
    value_score: str = Field(description="'High' | 'Very High'")
    risks: list[str] = Field(description="Top 2-3 technical or business risks")
    prerequisites: list[str] = Field(description="What the client must provide")
    addresses_use_case: str = Field(description="The use case ID this solution addresses")


class SolutionReport(BaseModel):
    """Structured output: solution cards for selected use cases."""
    solutions: list[SolutionCard] = Field(
        description="One solution card per selected use case"
    )
    recommendation: str = Field(
        description="Which solution to start with and why (1-2 sentences)"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def format_blueprints(docs: list[Document]) -> str:
    """Format retrieved blueprints as context string."""
    if not docs:
        return "No specific blueprints found — use general agency knowledge."
    return "\n\n---\n\n".join(
        f"[Blueprint {i+1}]\n{doc.page_content.strip()}"
        for i, doc in enumerate(docs)
    )


def get_selected_use_cases(all_use_cases: list[dict],
                            selected_ids: list[str] | None) -> list[dict]:
    """
    Return only the selected use cases.
    If no IDs specified, return the top 2 by confidence score.

    CONCEPT: Graceful Defaults
    In a production pipeline, the user explicitly selects use cases
    via the frontend UI. In CLI mode (no UI), we default to the top 2.
    Building in sensible defaults makes the system testable end-to-end
    without needing a full UI. This is a common pattern in pipeline design.
    """
    if not selected_ids:
        # Auto-select top 2 by confidence score
        sorted_cases = sorted(
            all_use_cases,
            key=lambda x: x.get("confidence_score", 0),
            reverse=True
        )
        return sorted_cases[:2]

    return [uc for uc in all_use_cases if uc.get("id") in selected_ids]


# ---------------------------------------------------------------------------
# The Solution Agent
# ---------------------------------------------------------------------------

def run_solution_agent(use_cases: list[dict],
                        selected_ids: list[str] | None = None) -> SolutionReport:
    """
    Generate solution cards for selected use cases.

    CONCEPT: Multi-Query RAG
    Unlike the Use Case Agent (one query for the whole report),
    here we run ONE retrieval query PER selected use case.
    This gives us the most relevant blueprints for each specific use case
    rather than a blended result for all of them at once.

    Then we send ALL retrieved blueprints + ALL use cases to Claude
    in a single prompt — one LLM call generates all solution cards.
    This is more efficient than one LLM call per use case.

    The trade-off:
      Multi-query retrieval + single generation  ← what we do (efficient)
      Single-query retrieval + multi generation  ← more LLM calls, slower
      Multi-query + multi generation             ← most thorough, most expensive
    """
    selected = get_selected_use_cases(use_cases, selected_ids)

    if not selected:
        raise ValueError("No use cases available for solution generation")

    print(f"\n[Solution Agent] Generating solutions for {len(selected)} use cases:")
    for uc in selected:
        print(f"  - {uc.get('title')} ({uc.get('confidence_score', 0):.0%})")

    retriever = get_solution_retriever(k=3)
    llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0.2)

    # CONCEPT: Per-Use-Case Multi-Query Retrieval
    # For each use case, build a focused query combining:
    #   - The use case title (most specific signal)
    #   - The tags (category context)
    #   - The description (broader semantic context)
    # Then deduplicate blueprints to avoid sending the same one twice.
    all_blueprints: list[Document] = []
    seen_contents: set[str] = set()

    for uc in selected:
        query = f"{uc.get('title', '')} {' '.join(uc.get('tags', []))} {uc.get('description', '')[:150]}"
        docs = retriever.invoke(query)
        for doc in docs:
            # Use first 100 chars as dedup key
            key = doc.page_content[:100]
            if key not in seen_contents:
                all_blueprints.append(doc)
                seen_contents.add(key)

    print(f"[Solution Agent] Retrieved {len(all_blueprints)} unique blueprints from KB")
    context = format_blueprints(all_blueprints)

    # Build use case summary for the prompt
    use_cases_text = "\n\n".join([
        f"USE CASE [{uc.get('id')}]: {uc.get('title')}\n"
        f"  Description: {uc.get('description')}\n"
        f"  Effort: {uc.get('effort_estimate')} | "
        f"Confidence: {uc.get('confidence_score', 0):.0%}\n"
        f"  Evidence: {'; '.join(uc.get('supporting_evidence', [])[:2])}"
        for uc in selected
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior solutions architect at a custom software development agency.
For each selected use case, design a concrete, deliverable technical solution.

Use the RETRIEVED BLUEPRINTS below as your starting point. Adapt them to the
specific context — don't just copy them verbatim. Every solution must:
  - Have a specific, realistic tech stack
  - Include phased delivery (show the client a clear path)
  - Be honest about risks and prerequisites
  - Be deliverable by a 2-3 person team in under 8 weeks

RETRIEVED BLUEPRINTS FROM AGENCY LIBRARY:
{blueprints}
"""),
        ("human", """Design solution cards for these selected use cases:

{use_cases}

Generate one SolutionCard per use case, plus a top-level recommendation
on which to start with first and why.""")
    ])

    structured_llm = llm.with_structured_output(SolutionReport)
    chain = prompt | structured_llm

    result: SolutionReport = chain.invoke({
        "blueprints": context,
        "use_cases": use_cases_text,
    })

    print(f"[Solution Agent] Generated {len(result.solutions)} solution cards")
    for sol in result.solutions:
        print(f"  [{sol.effort_score} effort | {sol.value_score} value] "
              f"{sol.title} ({sol.timeline})")

    return result


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json, asyncio
    from agents.ingestion_agent import scrape_website
    from agents.analysis_agent import run_analysis_agent
    from agents.use_case_agent import run_use_case_agent

    url = sys.argv[1] if len(sys.argv) > 1 else "https://stripe.com"

    print(f"\n{'='*60}")
    print(f"DivAi — Full Pipeline (Ingestion → Analysis → Use Cases → Solutions)")
    print(f"Target: {url}")
    print(f"{'='*60}")

    print("\n[1/4] Ingestion...")
    scrape = asyncio.run(scrape_website(url, "surface"))

    print("\n[2/4] Analysis...")
    report = run_analysis_agent(scrape).model_dump()

    print("\n[3/4] Use Cases...")
    use_case_result = run_use_case_agent(report)
    use_cases = [uc.model_dump() for uc in use_case_result.use_cases]

    print("\n[4/4] Solutions (top 2 use cases)...")
    solution_result = run_solution_agent(use_cases)

    print(f"\n{'='*60}")
    print("SOLUTION CARDS")
    print(f"{'='*60}")
    print(f"\nRecommendation: {solution_result.recommendation}\n")

    for sol in solution_result.solutions:
        print(f"\n{'─'*50}")
        print(f"  {sol.title}")
        print(f"  {sol.pitch}")
        print(f"  Timeline: {sol.timeline}  |  Effort: {sol.effort_score}  |  Value: {sol.value_score}")
        print(f"\n  Architecture:")
        print(f"  {sol.architecture_overview}")
        print(f"\n  Stack: {', '.join(sol.stack[:6])}")
        print(f"\n  Phases:")
        for phase in sol.phases:
            print(f"    {phase}")
        print(f"\n  Risks:")
        for risk in sol.risks:
            print(f"    - {risk}")
        print(f"\n  Prerequisites:")
        for prereq in sol.prerequisites:
            print(f"    - {prereq}")
