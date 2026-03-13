"""
DivAi — Use Case Agent (Phase 3)

WHAT THIS AGENT DOES:
  Takes an IntelligenceReport and generates ranked, scored business
  use cases by combining:
    1. RAG retrieval  — relevant templates from the agency knowledge base
    2. LangChain LCEL — structured prompt pipeline
    3. Claude         — reasoning and scoring against the actual signals

WHERE IT FITS IN DIVAI:
  Layer 2 — Intelligence Layer
  Third node in the LangGraph pipeline.
  Reads:  intelligence_report (from Analysis Agent)
  Writes: use_cases (read by Solution Agent)

CONCEPTS COVERED:
  - LangChain LCEL (| pipe operator for chaining components)
  - Retriever as a LangChain component
  - Prompt templates with dynamic context
  - Structured output with Pydantic + .with_structured_output()
  - Grounding LLM reasoning in retrieved knowledge
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough

from rag.knowledge_base import get_use_case_retriever

load_dotenv()


# ---------------------------------------------------------------------------
# Output Schema — what the Use Case Agent produces
# ---------------------------------------------------------------------------

class ScoredUseCase(BaseModel):
    """A single business use case with confidence scoring."""
    id: str = Field(description="Unique ID e.g. 'uc_001'")
    title: str = Field(description="Short, punchy title for the use case")
    description: str = Field(description="2-3 sentence explanation of the opportunity")
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="0.0-1.0. How strongly the website signals support this use case"
    )
    supporting_evidence: list[str] = Field(
        description="Specific signals from the report that justify this use case"
    )
    tags: list[str] = Field(description="Category tags e.g. ['AI/ML', 'SaaS', 'Automation']")
    effort_estimate: str = Field(description="'Low' | 'Medium' | 'High'")
    value_rating: str = Field(description="'High' | 'Very High'")


class UseCaseList(BaseModel):
    """Structured output: a ranked list of use cases."""
    use_cases: list[ScoredUseCase] = Field(
        description="List of use cases ranked by confidence score (highest first)"
    )
    analysis_summary: str = Field(
        description="1-2 sentence summary of the key opportunity themes identified"
    )


# ---------------------------------------------------------------------------
# Helper: format retrieved documents for the prompt
# ---------------------------------------------------------------------------

def format_retrieved_docs(docs: list[Document]) -> str:
    """
    Convert retrieved documents into a clean string for the prompt.

    CONCEPT: Context Formatting
    The retriever returns Document objects. The LLM prompt needs a string.
    This function bridges the two by joining document contents with separators.
    In LCEL chains, this function is used as a RunnableLambda — a step
    in the pipeline that transforms data.
    """
    if not docs:
        return "No specific templates retrieved — use general agency knowledge."

    formatted = []
    for i, doc in enumerate(docs, 1):
        formatted.append(f"[Template {i}]\n{doc.page_content.strip()}")

    return "\n\n---\n\n".join(formatted)


# ---------------------------------------------------------------------------
# Helper: build a query string from the IntelligenceReport
# ---------------------------------------------------------------------------

def build_retrieval_query(report: dict) -> str:
    """
    Convert an IntelligenceReport into a focused retrieval query.

    CONCEPT: Query Construction for RAG
    The retrieval query is critical — garbage in, garbage out.
    A poorly constructed query returns irrelevant templates.
    A focused query packs the most meaningful signals into a short string.

    We combine:
      - Business category (most important signal)
      - Key features (what the product actually does)
      - Integrations (reveals payment, analytics, support stack)
      - Tech stack (sometimes relevant e.g. "API-first platform")

    This query gets embedded and matched against template embeddings.
    Matching works on MEANING, not keywords — so "subscription management"
    will match templates about "SaaS churn" even without exact word overlap.
    """
    tech = report.get("tech_stack", {})
    parts = [
        report.get("business_category", ""),
        " ".join(report.get("key_features", [])[:5]),
        " ".join(report.get("integrations", [])),
        tech.get("frontend_framework", ""),
    ]
    return " ".join(p for p in parts if p).strip()


# ---------------------------------------------------------------------------
# The Use Case Agent
# ---------------------------------------------------------------------------

def run_use_case_agent(intelligence_report: dict) -> UseCaseList:
    """
    Generate ranked use cases from an IntelligenceReport using RAG + Claude.

    CONCEPT: The Full RAG + LangChain LCEL Pipeline
    ------------------------------------------------
    This function demonstrates the complete pattern:

    1. Build a query from the report signals
    2. Retrieve relevant use case templates from ChromaDB
    3. Format those templates as context
    4. Build a prompt with: context + report summary
    5. Call Claude with structured output (Pydantic schema)
    6. Return typed UseCaseList

    The LangChain LCEL chain looks like:
        retriever | format_docs    ← retrieval step
        |
        prompt                     ← template with {context} + {report}
        |
        llm.with_structured_output ← forces Pydantic output
        |
        UseCaseList                ← typed result

    CONCEPT: .with_structured_output()
    When you call llm.with_structured_output(Schema), LangChain:
      1. Converts the Pydantic schema to a tool definition
      2. Forces Claude to call that tool (so output is always valid JSON)
      3. Parses the tool call into a Pydantic object
    This is the cleanest way to get structured output from an LLM.
    """

    target_url = intelligence_report.get("target_url", "unknown")
    print(f"\n[UseCase Agent] Generating use cases for {target_url}")

    # Step 1: Build retrieval query from report signals
    query = build_retrieval_query(intelligence_report)
    print(f"[UseCase Agent] Retrieval query: {query[:100]}...")

    # Step 2: Set up retriever and LLM
    retriever = get_use_case_retriever(k=5)
    llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0.3)

    # CONCEPT: temperature parameter
    # Temperature controls how "creative" vs "consistent" the LLM is.
    # 0.0 = fully deterministic (same input → same output every time)
    # 1.0 = highly varied (same input → different output each time)
    # 0.3 = slightly creative but mostly consistent — good for analysis tasks
    # Use low temperature when you want reliable, consistent analysis.
    # Use higher temperature for creative writing or brainstorming.

    # Step 3: Retrieve relevant templates
    retrieved_docs = retriever.invoke(query)
    context = format_retrieved_docs(retrieved_docs)
    print(f"[UseCase Agent] Retrieved {len(retrieved_docs)} templates from KB")

    # Step 4: Build the summary of the intelligence report for the prompt
    # CONCEPT: Report Summarisation for Prompts
    # We don't dump the entire IntelligenceReport into the prompt.
    # We extract the most signal-dense fields to keep the prompt focused.
    tech = intelligence_report.get("tech_stack", {})
    report_summary = f"""
TARGET: {target_url}
BUSINESS CATEGORY: {intelligence_report.get('business_category', 'Unknown')}
FRAMEWORK: {tech.get('frontend_framework', 'Unknown')} ({tech.get('language', 'Unknown')})
KEY FEATURES: {', '.join(intelligence_report.get('key_features', []))}
INTEGRATIONS: {', '.join(intelligence_report.get('integrations', []))}
DATA MODELS: {', '.join(intelligence_report.get('data_models', []))}
AUTH PATTERN: {intelligence_report.get('auth_pattern', {}).get('method', 'Unknown')}
API ENDPOINTS: {len(intelligence_report.get('api_endpoints', []))} detected
UI PATTERNS: {', '.join(intelligence_report.get('ui_patterns', []))}
ANALYST NOTES: {intelligence_report.get('analyst_notes', '')[:300]}
""".strip()

    # Step 5: Build the prompt
    # CONCEPT: Prompt Template with RAG Context
    # The prompt has two sources of context:
    #   {context}  — retrieved templates from our knowledge base
    #   {report}   — the actual intelligence from this specific website
    # Claude's job: use the templates as a starting point, but score
    # each use case against the ACTUAL signals in the report.
    # This grounds the output in evidence, not hallucination.
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior business analyst at a custom software development agency.
Your job: identify the highest-value software development opportunities for a client based on
their website's technical intelligence report.

Use the RETRIEVED TEMPLATES below as a starting point — they represent proven use cases
the agency has delivered. For each use case you recommend:
  - It must be strongly supported by specific signals in the INTELLIGENCE REPORT
  - confidence_score must reflect evidence strength (not just plausibility)
  - supporting_evidence must cite specific signals from the report
  - Only recommend 3-6 use cases maximum — quality over quantity

RETRIEVED TEMPLATES FROM AGENCY KNOWLEDGE BASE:
{context}
"""),
        ("human", """Based on this intelligence report, identify the best use cases:

INTELLIGENCE REPORT:
{report}

Generate a ranked list of use cases with confidence scores. Be specific about evidence.""")
    ])

    # Step 6: Build the LCEL chain with structured output
    # CONCEPT: LCEL Chain Assembly
    # We build the chain manually (not using the pipe operator for retrieval)
    # because we've already done the retrieval step above.
    # The chain is: prompt | llm_with_schema
    # .with_structured_output() wraps the LLM to always return a UseCaseList
    structured_llm = llm.with_structured_output(UseCaseList)

    chain = prompt | structured_llm

    # Step 7: Invoke the chain
    result: UseCaseList = chain.invoke({
        "context": context,
        "report": report_summary,
    })

    # Sort by confidence score (highest first)
    result.use_cases.sort(key=lambda uc: uc.confidence_score, reverse=True)

    print(f"[UseCase Agent] Generated {len(result.use_cases)} use cases")
    for uc in result.use_cases:
        print(f"  [{uc.confidence_score:.0%}] {uc.title}")

    return result


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    from agents.ingestion_agent import scrape_website
    from agents.analysis_agent import run_analysis_agent
    import asyncio

    url = sys.argv[1] if len(sys.argv) > 1 else "https://stripe.com"

    print(f"\n{'='*60}")
    print(f"DivAi Use Case Agent")
    print(f"Target: {url}")
    print(f"{'='*60}")

    print("\n[1/3] Ingestion...")
    scrape = asyncio.run(scrape_website(url, "surface"))

    print("\n[2/3] Analysis...")
    report = run_analysis_agent(scrape)
    report_dict = report.model_dump()

    print("\n[3/3] Use Case Generation...")
    use_cases = run_use_case_agent(report_dict)

    print(f"\n{'='*60}")
    print("USE CASES IDENTIFIED")
    print(f"{'='*60}")
    print(f"\nSummary: {use_cases.analysis_summary}\n")

    for i, uc in enumerate(use_cases.use_cases, 1):
        print(f"\n[{i}] {uc.title}")
        print(f"     Confidence: {uc.confidence_score:.0%} | "
              f"Effort: {uc.effort_estimate} | Value: {uc.value_rating}")
        print(f"     Tags: {', '.join(uc.tags)}")
        print(f"     {uc.description}")
        print(f"     Evidence:")
        for ev in uc.supporting_evidence:
            print(f"       - {ev}")
