"""
DivAi — Analysis Agent (Phase 1, Week 2)

WHAT THIS AGENT DOES:
  Takes the raw scrape data from the Ingestion Agent and uses Claude
  with structured tool calls to produce a typed IntelligenceReport.

  Raw data in → Structured intelligence out.

WHERE IT FITS IN DIVAI:
  Layer 2 — Intelligence Layer
  Second node in the LangGraph pipeline.
  Reads:  raw_dom, network_log, tech_signals (from Ingestion Agent)
  Writes: intelligence_report (read by Use Case Agent)

CONCEPTS COVERED:
  - Pre-processing: why we summarise before sending to Claude
  - Tool use as a structured output mechanism
  - The agent loop (same pattern as Phase 2 of the guide)
  - Pydantic models for validated structured output
"""

import json
import anthropic
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()


# ---------------------------------------------------------------------------
# Output Schema — what the Analysis Agent produces
# ---------------------------------------------------------------------------
# CONCEPT: Output Schema Design
# Before writing the agent, define exactly what you want out of it.
# This forces clarity: what does "analysis" actually mean in concrete terms?
# Each field answers a specific business question the Use Case Agent will need.

class TechStack(BaseModel):
    frontend_framework: str             # e.g. "Next.js / React"
    language: str                       # e.g. "JavaScript / TypeScript"
    hosting_signals: list[str]          # e.g. ["Vercel", "CloudFront CDN"]
    database_signals: list[str]         # e.g. ["PostgreSQL (inferred from API patterns)"]
    confidence: float = Field(ge=0.0, le=1.0)  # How confident is the classification


class DetectedEndpoint(BaseModel):
    method: str                 # GET, POST, PUT, DELETE
    url_pattern: str            # e.g. "/api/v1/users/{id}"
    inferred_purpose: str       # e.g. "User profile retrieval"
    data_signals: list[str]     # e.g. ["user_id", "email", "created_at"]


class AuthPattern(BaseModel):
    method: str                 # "JWT Bearer" | "Session Cookie" | "OAuth2" | "API Key"
    providers: list[str]        # e.g. ["Google", "GitHub"] for OAuth
    token_refresh: bool         # Does the app use token refresh patterns?
    notes: str                  # Any interesting auth observations


class IntelligenceReport(BaseModel):
    """
    The structured output of the Analysis Agent.
    This is what gets stored in DivAiState.intelligence_report
    and read by the Use Case Agent to generate business opportunities.
    """
    target_url: str
    tech_stack: TechStack
    api_endpoints: list[DetectedEndpoint]
    auth_pattern: AuthPattern
    ui_patterns: list[str]          # e.g. ["SaaS dashboard", "Marketing landing page"]
    integrations: list[str]         # e.g. ["Stripe", "Intercom", "Segment"]
    data_models: list[str]          # Inferred e.g. ["User", "Subscription", "Invoice"]
    business_category: str          # e.g. "FinTech SaaS", "E-commerce", "Marketplace"
    key_features: list[str]         # e.g. ["Payment processing", "User auth", "Analytics"]
    analyst_notes: str              # Free-form observations from Claude


# ---------------------------------------------------------------------------
# Pre-processor — compact the raw scrape data before sending to Claude
# ---------------------------------------------------------------------------
# CONCEPT: Pre-processing for LLMs
# Raw HTML is full of noise: CSS classes, SVG paths, tracking pixels.
# Before sending data to Claude we extract only the SIGNAL — the meaningful parts.
# This reduces token usage by ~95% and makes Claude's job much easier.
# Think of it as preparing a briefing document instead of handing someone
# a raw 50MB log file.

def preprocess_scrape_data(scrape_result: dict) -> str:
    """
    Convert raw scrape data into a compact analysis briefing for Claude.
    Returns a string of ~2000-4000 tokens instead of hundreds of thousands.
    """
    dom = scrape_result.get("dom", {})
    network_log = scrape_result.get("network_log", [])
    tech_signals = scrape_result.get("tech_signals", {})
    metadata = scrape_result.get("metadata", {})

    # --- Summarise network requests ---
    # Group by type and keep only unique URL patterns (strip IDs/hashes)
    api_calls = [r for r in network_log if r["resource_type"] in ("fetch", "xhr")]
    doc_calls = [r for r in network_log if r["resource_type"] == "document"]
    script_srcs = dom.get("external_scripts", [])

    # Deduplicate script sources (many are CDN chunks — keep domain + path only)
    unique_script_domains = list(set(
        s.split("/")[2] for s in script_srcs if s.startswith("http")
    ))[:20]  # Cap at 20

    # Keep first 30 API calls — enough signal, not overwhelming
    api_summary = [
        f"{r['method']} {r['url'][:120]}" for r in api_calls[:30]
    ]

    # --- Forms (reveal app features) ---
    forms = dom.get("forms", [])
    form_summary = []
    for form in forms[:10]:  # Cap at 10 forms
        fields = [f.get("name") or f.get("placeholder") or f.get("type")
                  for f in form.get("fields", []) if f.get("name") or f.get("placeholder")]
        if fields:
            form_summary.append(f"Form ({form.get('method', 'GET')}): fields={fields}")

    # --- Build the briefing string ---
    briefing = f"""
WEBSITE ANALYSIS BRIEFING
==========================
URL: {scrape_result.get('target_url')}
Title: {metadata.get('title')}
Description: {metadata.get('description', '')[:200]}

DOM SUMMARY:
- Element counts: {dom.get('element_counts', {})}
- Forms detected: {len(forms)}
{chr(10).join(form_summary) if form_summary else '  (no forms)'}

TECH SIGNALS (pre-detected):
- Frameworks: {tech_signals.get('frameworks', [])}
- CSS frameworks: {tech_signals.get('css_frameworks', [])}
- Auth hints: {tech_signals.get('auth_hints', [])}
- Integrations: {tech_signals.get('integrations', [])}

NETWORK ACTIVITY:
- Total requests: {len(network_log)}
- API/XHR calls: {len(api_calls)}
- Document requests: {len(doc_calls)}

API CALLS OBSERVED (first 30):
{chr(10).join(f'  {a}' for a in api_summary) if api_summary else '  (none detected)'}

SCRIPT SOURCES (unique domains):
{chr(10).join(f'  {d}' for d in unique_script_domains) if unique_script_domains else '  (none)'}
""".strip()

    return briefing


# ---------------------------------------------------------------------------
# Tool definitions — what Claude can call
# ---------------------------------------------------------------------------
# CONCEPT: Tool Schema Design for Structured Output
# We define tools not because we need Claude to "do" something external,
# but to force it to return data in a specific structure.
# When Claude calls classify_tech_stack, it must fill every field in the schema.
# This is a common pattern: use tool calling as a structured output mechanism.

ANALYSIS_TOOLS = [
    {
        "name": "classify_tech_stack",
        "description": (
            "Classify the technology stack used by the website based on the briefing data. "
            "Call this FIRST."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "frontend_framework": {
                    "type": "string",
                    "description": "Primary frontend framework e.g. 'Next.js / React', 'Vue 3', 'Angular'"
                },
                "language": {
                    "type": "string",
                    "description": "Primary language e.g. 'TypeScript', 'JavaScript', 'Python'"
                },
                "hosting_signals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Inferred hosting/CDN e.g. ['Vercel', 'AWS CloudFront']"
                },
                "database_signals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Inferred databases from API patterns e.g. ['PostgreSQL']"
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence score 0.0-1.0"
                }
            },
            "required": ["frontend_framework", "language", "hosting_signals",
                         "database_signals", "confidence"]
        }
    },
    {
        "name": "extract_api_endpoints",
        "description": (
            "Extract and classify the API endpoints observed in network traffic. "
            "Infer their purpose from URL patterns and HTTP methods."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "endpoints": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "method":           {"type": "string"},
                            "url_pattern":      {"type": "string"},
                            "inferred_purpose": {"type": "string"},
                            "data_signals":     {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["method", "url_pattern", "inferred_purpose", "data_signals"]
                    }
                }
            },
            "required": ["endpoints"]
        }
    },
    {
        "name": "detect_auth_pattern",
        "description": "Identify the authentication and authorisation patterns used.",
        "input_schema": {
            "type": "object",
            "properties": {
                "method":        {"type": "string",
                                  "description": "e.g. 'JWT Bearer', 'Session Cookie', 'OAuth2', 'API Key'"},
                "providers":     {"type": "array", "items": {"type": "string"},
                                  "description": "OAuth providers e.g. ['Google', 'GitHub']"},
                "token_refresh": {"type": "boolean"},
                "notes":         {"type": "string"}
            },
            "required": ["method", "providers", "token_refresh", "notes"]
        }
    },
    {
        "name": "finalize_report",
        "description": (
            "Call this LAST to complete the intelligence report. "
            "Synthesise all previous tool results into a final assessment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ui_patterns": {
                    "type": "array", "items": {"type": "string"},
                    "description": "e.g. ['SaaS dashboard', 'Marketing site', 'E-commerce store']"
                },
                "data_models": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Inferred data models e.g. ['User', 'Subscription', 'Invoice']"
                },
                "business_category": {
                    "type": "string",
                    "description": "e.g. 'FinTech SaaS', 'E-commerce', 'Developer Tools'"
                },
                "key_features": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Core product features detected"
                },
                "analyst_notes": {
                    "type": "string",
                    "description": "Key observations and anything interesting worth flagging"
                }
            },
            "required": ["ui_patterns", "data_models", "business_category",
                         "key_features", "analyst_notes"]
        }
    }
]


# ---------------------------------------------------------------------------
# The Analysis Agent — the tool-use loop
# ---------------------------------------------------------------------------

def run_analysis_agent(scrape_result: dict) -> IntelligenceReport:
    """
    Run the Analysis Agent against a scrape result.

    CONCEPT: The Tool-Use Agent Loop
    This is the exact same pattern as Phase 2 of the AI Development Guide,
    but now applied to a real DivAi task.

    Loop:
      1. Send briefing + tool definitions to Claude
      2. Claude calls a tool (returns stop_reason='tool_use')
      3. We "execute" the tool (here: just capture its structured input)
      4. Feed the result back into the conversation
      5. Claude calls the next tool
      6. Repeat until Claude calls finalize_report
      7. Extract the IntelligenceReport from all tool call results

    The key insight: Claude is acting as a structured reasoning engine.
    It reads the briefing, thinks through the analysis, and expresses its
    conclusions by calling tools with the right fields filled in.
    """

    target_url = scrape_result.get("target_url", "")
    briefing = preprocess_scrape_data(scrape_result)

    print(f"\n[Analysis] Starting analysis for: {target_url}")
    print(f"[Analysis] Briefing size: {len(briefing)} chars")

    # Storage for tool call results — we accumulate these as Claude calls tools
    tool_results_store = {
        "tech_stack": None,
        "api_endpoints": [],
        "auth_pattern": None,
        "final": None,
    }

    # CONCEPT: The System Prompt for an Analysis Agent
    # The system prompt sets the agent's role and constraints.
    # "You MUST call all tools" forces structured output — Claude can't
    # skip straight to a text answer.
    system_prompt = """You are a senior software architect performing technical due diligence
on a website for a software development agency. Your job is to analyse the provided
briefing and extract structured intelligence.

You MUST call the tools in this order:
  1. classify_tech_stack
  2. extract_api_endpoints
  3. detect_auth_pattern
  4. finalize_report

Be precise and specific. Base conclusions on evidence in the briefing.
If something is uncertain, say so in the confidence score or notes."""

    messages = [
        {"role": "user", "content": f"Please analyse this website briefing:\n\n{briefing}"}
    ]

    step = 0

    # The agent loop
    while True:
        step += 1
        print(f"[Analysis] Agent step {step}...")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            tools=ANALYSIS_TOOLS,
            messages=messages
        )

        # If Claude finished with text (shouldn't happen with tool_choice=required)
        if response.stop_reason == "end_turn":
            print("[Analysis] Agent completed via end_turn")
            break

        # Claude wants to call a tool
        if response.stop_reason == "tool_use":
            # Add Claude's response to conversation history
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                tool_name = block.name
                tool_input = block.input
                print(f"[Analysis] Tool called: {tool_name}")

                # CONCEPT: Tool Execution
                # In a real tool-use agent, we'd call external APIs here.
                # For analysis tools, the "execution" is just capturing the
                # structured data Claude filled in — Claude IS the tool.
                # We validate it with Pydantic to catch any type errors.

                if tool_name == "classify_tech_stack":
                    tool_results_store["tech_stack"] = TechStack(**tool_input)
                    result_content = "Tech stack classification saved."

                elif tool_name == "extract_api_endpoints":
                    endpoints = [
                        DetectedEndpoint(**ep)
                        for ep in tool_input.get("endpoints", [])
                    ]
                    tool_results_store["api_endpoints"] = endpoints
                    result_content = f"{len(endpoints)} API endpoints extracted."

                elif tool_name == "detect_auth_pattern":
                    tool_results_store["auth_pattern"] = AuthPattern(**tool_input)
                    result_content = "Auth pattern detected."

                elif tool_name == "finalize_report":
                    tool_results_store["final"] = tool_input
                    result_content = "Report finalised."

                else:
                    result_content = f"Unknown tool: {tool_name}"

                # Feed the result back so Claude knows the tool succeeded
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_content
                })

            messages.append({"role": "user", "content": tool_results})

            # Stop once finalize_report has been called
            if tool_results_store["final"] is not None:
                print("[Analysis] All tools called. Building report.")
                break

    # ---------------------------------------------------------------------------
    # Assemble the final IntelligenceReport from all tool results
    # ---------------------------------------------------------------------------
    final = tool_results_store["final"] or {}
    integrations = scrape_result.get("tech_signals", {}).get("integrations", [])

    report = IntelligenceReport(
        target_url=target_url,
        tech_stack=tool_results_store["tech_stack"] or TechStack(
            frontend_framework="Unknown",
            language="Unknown",
            hosting_signals=[],
            database_signals=[],
            confidence=0.0
        ),
        api_endpoints=tool_results_store["api_endpoints"],
        auth_pattern=tool_results_store["auth_pattern"] or AuthPattern(
            method="Unknown",
            providers=[],
            token_refresh=False,
            notes=""
        ),
        ui_patterns=final.get("ui_patterns", []),
        integrations=integrations,
        data_models=final.get("data_models", []),
        business_category=final.get("business_category", "Unknown"),
        key_features=final.get("key_features", []),
        analyst_notes=final.get("analyst_notes", ""),
    )

    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from ingestion_agent import scrape_website
    import asyncio

    url = sys.argv[1] if len(sys.argv) > 1 else "https://stripe.com"

    print(f"\n{'='*60}")
    print(f"DivAi Analysis Agent")
    print(f"Target: {url}")
    print(f"{'='*60}")

    # Step 1: Scrape
    print("\n[Step 1] Running Ingestion Agent...")
    scrape_result = asyncio.run(scrape_website(url, "surface"))

    # Step 2: Analyse
    print("\n[Step 2] Running Analysis Agent...")
    report = run_analysis_agent(scrape_result)

    # Step 3: Print structured report
    print(f"\n{'='*60}")
    print("INTELLIGENCE REPORT")
    print(f"{'='*60}")
    print(f"URL:               {report.target_url}")
    print(f"Business Category: {report.business_category}")
    print(f"\nTECH STACK:")
    print(f"  Framework:  {report.tech_stack.frontend_framework}")
    print(f"  Language:   {report.tech_stack.language}")
    print(f"  Hosting:    {report.tech_stack.hosting_signals}")
    print(f"  Confidence: {report.tech_stack.confidence:.0%}")
    print(f"\nAUTH PATTERN:")
    print(f"  Method:    {report.auth_pattern.method}")
    print(f"  Providers: {report.auth_pattern.providers}")
    print(f"  Notes:     {report.auth_pattern.notes}")
    print(f"\nAPI ENDPOINTS ({len(report.api_endpoints)} detected):")
    for ep in report.api_endpoints[:8]:
        print(f"  {ep.method:6} {ep.url_pattern:50} | {ep.inferred_purpose}")
    print(f"\nDATA MODELS:   {report.data_models}")
    print(f"KEY FEATURES:  {report.key_features}")
    print(f"INTEGRATIONS:  {report.integrations}")
    print(f"UI PATTERNS:   {report.ui_patterns}")
    print(f"\nANALYST NOTES:\n{report.analyst_notes}")

    # Save to JSON
    output_path = f"output_analysis_{report.target_url.replace('https://', '').replace('/', '_')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)
    print(f"\n[Analysis] Report saved to: {output_path}")
