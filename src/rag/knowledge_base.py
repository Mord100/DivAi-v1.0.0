"""
DivAi — Knowledge Base Seeder (Phase 3)

WHAT THIS FILE DOES:
  Seeds ChromaDB with use case templates.
  Run this ONCE to build the knowledge base.
  After that, the Use Case Agent queries it on every analysis.

CONCEPT: The Two Phases of RAG
---------------------------------
RAG has two completely separate phases that happen at different times:

  INDEXING (this file — run once):
    1. Load your knowledge documents
    2. Split them into chunks
    3. Convert each chunk to an embedding (list of numbers)
    4. Store embeddings + text in ChromaDB

  QUERYING (use_case_agent.py — runs per analysis):
    1. Convert your query to an embedding
    2. ChromaDB finds the chunks with the most similar embeddings
    3. Return those chunks as context for the LLM

CONCEPT: Why Chunk Documents?
--------------------------------
LLMs have limited context windows. If you have 100 templates and need
to find the 5 relevant ones, you can't stuff all 100 into every prompt.
Chunking + vector search lets you find the 5 relevant ones out of 100
in milliseconds, then only send those 5 to Claude.

Think of it like a librarian:
  Without RAG: pile every book on the table and say "find the answer"
  With RAG:    the librarian fetches the 3 most relevant books for you
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_voyageai import VoyageAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Path where ChromaDB will persist data between runs
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "../../data/chroma")


# ---------------------------------------------------------------------------
# Use Case Knowledge Base — agency-validated signal → opportunity mappings
# ---------------------------------------------------------------------------
# CONCEPT: Designing RAG Documents
# Each document is a use case template with:
#   - Trigger signals: what website patterns indicate this opportunity
#   - The opportunity itself: what we would build
#   - Value proposition: why the client should care
#   - Tech approach: how we'd build it (briefly)
#
# The metadata fields (category, effort, value) allow filtered retrieval:
# "give me only High value, E-commerce use cases"

USE_CASE_TEMPLATES = [

    # ── E-COMMERCE ──────────────────────────────────────────────────────────

    Document(
        page_content="""
USE CASE: AI-Powered Product Recommendation Engine
TRIGGER SIGNALS: E-commerce platform, product catalogue API endpoints,
  user session tracking, cart/checkout flows, Stripe payment integration.
OPPORTUNITY: Build a personalised recommendation engine that increases
  average order value and reduces cart abandonment. Uses collaborative
  filtering and real-time behavioural data to surface relevant products
  for each user at key conversion moments (cart, checkout, post-purchase).
VALUE: Typical 15–30% increase in average order value. Measurable
  within 30 days of deployment.
TECH APPROACH: Python ML pipeline (scikit-learn or TensorFlow),
  recommendation API, A/B testing framework, real-time event streaming.
EVIDENCE NEEDED: Product catalogue, user session data, purchase history.
""",
        metadata={"category": "E-commerce", "effort": "High",
                  "value": "Very High", "id": "uc_ecom_recommendations"}
    ),

    Document(
        page_content="""
USE CASE: Cart Abandonment Recovery Automation
TRIGGER SIGNALS: E-commerce checkout flow, email integration (Klaviyo,
  Mailchimp), Stripe payment gateway, user authentication.
OPPORTUNITY: Automated multi-step cart recovery workflow triggered when
  users add items but don't complete purchase. Personalised email
  sequences with dynamic product images and time-limited incentives.
VALUE: Recover 5–15% of abandoned carts. Low implementation effort,
  high ROI for any e-commerce business with >500 monthly transactions.
TECH APPROACH: Event-driven architecture, email API integration,
  workflow automation engine, personalisation layer.
EVIDENCE NEEDED: Cart/checkout API, email provider integration.
""",
        metadata={"category": "E-commerce", "effort": "Medium",
                  "value": "High", "id": "uc_ecom_cart_recovery"}
    ),

    Document(
        page_content="""
USE CASE: Inventory Intelligence & Demand Forecasting
TRIGGER SIGNALS: E-commerce or retail platform, product/inventory API
  endpoints, order management system, supplier/fulfilment integrations.
OPPORTUNITY: ML-powered demand forecasting that predicts stock needs
  per SKU, reduces overstock costs, and prevents stockouts. Includes
  automated reorder triggers and supplier notification system.
VALUE: Reduce inventory holding costs by 20–40%. Prevent revenue loss
  from stockouts during peak periods.
TECH APPROACH: Time-series forecasting (Prophet or LSTM), inventory
  management API, automated alerting, dashboard.
EVIDENCE NEEDED: Historical order data, product catalogue, inventory API.
""",
        metadata={"category": "E-commerce", "effort": "High",
                  "value": "Very High", "id": "uc_ecom_inventory"}
    ),

    # ── FINTECH / SAAS ───────────────────────────────────────────────────────

    Document(
        page_content="""
USE CASE: Subscription Churn Prediction & Retention Engine
TRIGGER SIGNALS: SaaS platform with subscription billing (Stripe
  Subscriptions, Chargebee, Recurly), user activity tracking, login
  frequency patterns, support ticket integration.
OPPORTUNITY: ML model that predicts churn probability per subscriber
  30–60 days in advance. Triggers personalised retention workflows:
  success manager outreach, product tips, feature unlocks, or discount
  offers based on churn risk score.
VALUE: Reducing churn by even 1% compounds significantly. For a
  $1M ARR business, 1% churn reduction = ~$10K additional ARR.
TECH APPROACH: Classification model (XGBoost), feature engineering
  from product usage data, automated CRM workflow, A/B tested
  retention playbooks.
EVIDENCE NEEDED: Subscription API, user activity events, churn history.
""",
        metadata={"category": "SaaS", "effort": "High",
                  "value": "Very High", "id": "uc_saas_churn"}
    ),

    Document(
        page_content="""
USE CASE: AI-Powered Customer Support Automation
TRIGGER SIGNALS: Live chat widget (Intercom, Drift, Zendesk),
  support ticket system, help centre / knowledge base, FAQ pages,
  high volume of repetitive support requests.
OPPORTUNITY: Conversational AI agent that handles Tier-1 support
  queries autonomously (password reset, billing questions, order status,
  feature how-tos). Escalates to human agents only for complex issues.
  Trained on existing help docs and historical ticket resolutions.
VALUE: Deflect 40–60% of support tickets. Reduce support team cost
  while improving response time from hours to seconds.
TECH APPROACH: RAG over knowledge base, Claude API, chat widget
  integration, escalation logic, human handoff protocol.
EVIDENCE NEEDED: Existing help docs, chat widget integration, ticket API.
""",
        metadata={"category": "SaaS", "effort": "Medium",
                  "value": "High", "id": "uc_saas_support_ai"}
    ),

    Document(
        page_content="""
USE CASE: Payment Fraud Detection & Risk Scoring
TRIGGER SIGNALS: Payment processing (Stripe, Braintree, Adyen),
  transaction API endpoints, user identity data, IP geolocation,
  financial platform or marketplace with high transaction volume.
OPPORTUNITY: Real-time fraud scoring model that evaluates each
  transaction before processing. Flags high-risk transactions for
  manual review or automatic decline. Reduces chargebacks and fraud losses.
VALUE: Fraud typically costs 0.5–1.5% of revenue. A model reducing
  fraud by 50% has clear, measurable ROI.
TECH APPROACH: Real-time ML scoring API, feature engineering from
  transaction patterns, rule engine overlay, case management UI.
EVIDENCE NEEDED: Transaction history, user behaviour data, chargeback records.
""",
        metadata={"category": "FinTech", "effort": "High",
                  "value": "Very High", "id": "uc_fintech_fraud"}
    ),

    Document(
        page_content="""
USE CASE: Self-Serve Analytics Dashboard & Reporting
TRIGGER SIGNALS: SaaS platform with business data, REST API with
  metrics/reporting endpoints, multi-tenant architecture, customer
  accounts with their own data sets.
OPPORTUNITY: Embeddable analytics dashboard that lets customers explore
  their own data without leaving the product. Reduces support load
  ("can you pull this report for me?") and increases product stickiness.
VALUE: Analytics features increase retention by 15–25% on average.
  Eliminates manual reporting requests to customer success teams.
TECH APPROACH: Embedded BI (Metabase, Apache Superset, or custom React
  charts), data API layer, row-level security per tenant.
EVIDENCE NEEDED: Data API endpoints, multi-tenant user model.
""",
        metadata={"category": "SaaS", "effort": "Medium",
                  "value": "High", "id": "uc_saas_analytics"}
    ),

    # ── DEVELOPER TOOLS ──────────────────────────────────────────────────────

    Document(
        page_content="""
USE CASE: Developer Portal with API Documentation & Sandbox
TRIGGER SIGNALS: Public API endpoints, developer-focused product,
  API key authentication, technical documentation, SDK downloads,
  developer sign-up flow.
OPPORTUNITY: Comprehensive developer portal: interactive API docs
  (OpenAPI/Swagger), live request sandbox, code examples in 5+
  languages, API key management console, usage analytics.
VALUE: Reduces developer onboarding time from days to hours.
  Self-service portal cuts developer support requests by 60%.
  Critical for API-first products with external developers.
TECH APPROACH: OpenAPI spec generation, interactive docs (Stoplight,
  Redoc, or custom), sandbox environment, API key dashboard.
EVIDENCE NEEDED: Existing API structure, developer sign-up flow, docs.
""",
        metadata={"category": "Developer Tools", "effort": "Medium",
                  "value": "High", "id": "uc_devtools_portal"}
    ),

    Document(
        page_content="""
USE CASE: CI/CD Pipeline Automation & Developer Workflow
TRIGGER SIGNALS: GitHub/GitLab integration, deployment scripts,
  Docker/Kubernetes signals, multi-environment setup (staging/production),
  engineering team with manual deployment processes.
OPPORTUNITY: Automated CI/CD pipeline: test → build → deploy to
  staging → smoke tests → promote to production. Includes rollback
  capability, deployment notifications, and environment promotion gates.
VALUE: Reduce deployment time from hours to minutes. Eliminate manual
  deployment errors. Enable multiple deploys per day safely.
TECH APPROACH: GitHub Actions or GitLab CI, Docker, infrastructure
  as code (Terraform), automated testing, Slack/Teams notifications.
EVIDENCE NEEDED: Current deployment process, GitHub/GitLab usage, infra stack.
""",
        metadata={"category": "Developer Tools", "effort": "Medium",
                  "value": "High", "id": "uc_devtools_cicd"}
    ),

    # ── MARKETPLACE ──────────────────────────────────────────────────────────

    Document(
        page_content="""
USE CASE: Smart Matching Algorithm for Marketplace
TRIGGER SIGNALS: Two-sided marketplace (buyers and sellers/providers),
  search and filter functionality, listing/profile pages, rating/review
  system, matching or booking flow.
OPPORTUNITY: ML-powered matching algorithm that pairs supply and demand
  based on multiple signals: location, preferences, historical ratings,
  availability, price fit, and behavioural patterns.
VALUE: Better matches → higher completion rates → more revenue.
  Typical 20–35% improvement in match quality over keyword search.
TECH APPROACH: Collaborative filtering, content-based features,
  ranking model, A/B testing framework, search API integration.
EVIDENCE NEEDED: Matching/search API, user profiles, historical matches.
""",
        metadata={"category": "Marketplace", "effort": "High",
                  "value": "Very High", "id": "uc_marketplace_matching"}
    ),

    Document(
        page_content="""
USE CASE: Dynamic Pricing Engine
TRIGGER SIGNALS: Marketplace or e-commerce platform with variable
  pricing, supply/demand signals, competitor pricing data (scraped or
  API), booking/reservation system.
OPPORTUNITY: Automated dynamic pricing that adjusts prices in real-time
  based on demand, inventory levels, competitor prices, and time factors.
  Maximises revenue during peak demand and drives volume during quiet periods.
VALUE: Dynamic pricing typically increases revenue by 10–25% vs fixed pricing.
TECH APPROACH: Pricing model (rule-based + ML hybrid), real-time
  price update API, competitor monitoring, A/B price testing.
EVIDENCE NEEDED: Current pricing model, demand/booking data, competitor visibility.
""",
        metadata={"category": "Marketplace", "effort": "High",
                  "value": "Very High", "id": "uc_marketplace_pricing"}
    ),

    # ── AI / AUTOMATION ──────────────────────────────────────────────────────

    Document(
        page_content="""
USE CASE: Document Intelligence & Data Extraction Pipeline
TRIGGER SIGNALS: Document upload functionality (PDFs, invoices, contracts),
  manual data entry processes, OCR or parsing mentions, admin/back-office
  workflows, form-heavy processes.
OPPORTUNITY: AI pipeline that automatically extracts structured data
  from unstructured documents: invoices → line items + totals,
  contracts → key clauses + dates, forms → structured records.
  Eliminates manual data entry entirely.
VALUE: Remove 80–90% of manual data entry time. Eliminate human
  transcription errors. Process documents in seconds vs hours.
TECH APPROACH: OCR pipeline, LLM extraction (Claude API), structured
  output validation (Pydantic), review/correction UI.
EVIDENCE NEEDED: Document types used, current manual process, data destinations.
""",
        metadata={"category": "AI/Automation", "effort": "Medium",
                  "value": "High", "id": "uc_ai_document_extraction"}
    ),

    Document(
        page_content="""
USE CASE: Personalised Content & Email Generation at Scale
TRIGGER SIGNALS: Email marketing platform (Klaviyo, Mailchimp,
  HubSpot), CRM integration, customer segmentation, large contact
  database, content-heavy product or marketing operation.
OPPORTUNITY: AI content generation pipeline that creates personalised
  email copy, product descriptions, or marketing content tailored to
  each customer segment, lifecycle stage, or individual. Human reviews
  and approves batches before send.
VALUE: Personalised content delivers 6x higher transaction rates than
  generic content. Reduce content production time by 70%.
TECH APPROACH: Claude API for generation, template system,
  personalisation variables, human-in-the-loop review UI, CRM integration.
EVIDENCE NEEDED: Current email/content workflow, CRM data, segmentation logic.
""",
        metadata={"category": "AI/Automation", "effort": "Low",
                  "value": "High", "id": "uc_ai_content_generation"}
    ),

    # ── INTERNAL OPERATIONS ─────────────────────────────────────────────────

    Document(
        page_content="""
USE CASE: Internal Admin Panel & Operations Dashboard
TRIGGER SIGNALS: Multi-tenant SaaS, user management API, subscription
  management, large internal team, manual admin tasks, customer support
  requiring data access.
OPPORTUNITY: Internal admin panel giving the operations team full
  visibility and control: user management, subscription overrides,
  feature flag management, billing adjustments, activity logs.
VALUE: Reduce engineering time spent on one-off admin requests by 80%.
  Empower operations team to self-serve on common tasks.
TECH APPROACH: Admin panel framework (React Admin, Retool, or custom),
  role-based access, audit logging, internal API.
EVIDENCE NEEDED: Current admin workflows, internal team pain points, data model.
""",
        metadata={"category": "Internal Ops", "effort": "Low",
                  "value": "High", "id": "uc_ops_admin_panel"}
    ),

    Document(
        page_content="""
USE CASE: Real-Time Monitoring, Alerting & Observability Platform
TRIGGER SIGNALS: Production application with API endpoints, error
  tracking (Sentry), logging infrastructure, microservices or complex
  architecture, engineering team without centralised monitoring.
OPPORTUNITY: Unified observability platform: error rate monitoring,
  API latency tracking, custom business metric alerts, on-call
  escalation, incident timeline view.
VALUE: Reduce mean time to detect (MTTD) and resolve (MTTR) incidents.
  Proactive alerts before customers report issues.
TECH APPROACH: OpenTelemetry instrumentation, metrics pipeline
  (Prometheus/Grafana or Datadog), alert manager, incident runbook system.
EVIDENCE NEEDED: Current monitoring gaps, incident history, infrastructure stack.
""",
        metadata={"category": "Internal Ops", "effort": "Medium",
                  "value": "High", "id": "uc_ops_monitoring"}
    ),
]


# ---------------------------------------------------------------------------
# Seeding function
# ---------------------------------------------------------------------------

def seed_use_case_kb(force_rebuild: bool = False) -> Chroma:
    """
    Seed ChromaDB with use case templates and return the vectorstore.

    Args:
        force_rebuild: If True, delete existing collection and rebuild.
                       Set True when you add new templates.

    Returns:
        A ChromaDB vectorstore ready for querying.

    CONCEPT: Persistent vs In-Memory Vector Store
    ChromaDB can run in two modes:
      1. In-memory: fast, but lost when the process ends
      2. Persistent (persist_directory): saved to disk, survives restarts

    We use persistent mode so we don't re-embed 5000 tokens every run.
    The first run embeds and saves. Every subsequent run loads instantly.
    """
    print("[KB] Loading embedding model...")

    # VoyageAI provides API-based embeddings — no local model or PyTorch needed.
    # voyage-3-lite is fast, cheap, and well-suited for short semantic chunks.
    embeddings = VoyageAIEmbeddings(model="voyage-3-lite")

    collection_name = "use_case_kb"
    persist_dir = os.path.abspath(CHROMA_DIR)

    # Check if collection already exists (avoid re-embedding on every run)
    if not force_rebuild:
        try:
            existing = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=persist_dir,
            )
            count = existing._collection.count()
            if count > 0:
                print(f"[KB] Loaded existing use_case_kb ({count} chunks)")
                return existing
        except Exception:
            pass  # Collection doesn't exist yet — build it

    # CONCEPT: Text Splitting
    # Even though our templates are already short, we split them for
    # consistency and to demonstrate the pattern used with longer docs.
    # chunk_size=600 means each chunk is at most 600 characters.
    # chunk_overlap=50 means adjacent chunks share 50 characters —
    # this prevents a sentence from being split across chunks with no context.
    print(f"[KB] Building use_case_kb with {len(USE_CASE_TEMPLATES)} templates...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(USE_CASE_TEMPLATES)
    print(f"[KB] Split into {len(chunks)} chunks")

    # CONCEPT: Chroma.from_documents()
    # This single call does three things:
    #   1. Calls embeddings.embed_documents() on every chunk
    #   2. Stores the text + embedding + metadata in ChromaDB
    #   3. Returns a Chroma object ready for .similarity_search()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=persist_dir,
    )

    print(f"[KB] use_case_kb seeded with {vectorstore._collection.count()} vectors")
    return vectorstore


def get_use_case_retriever(k: int = 5):
    """
    Get a LangChain retriever for the use case knowledge base.

    Args:
        k: Number of most-relevant chunks to return per query.

    Returns:
        A LangChain retriever that can be used in LCEL chains.

    CONCEPT: LangChain Retriever
    A retriever is a LangChain abstraction over any search mechanism.
    It has a single method: .invoke(query) → list[Document]
    This makes it composable in LCEL chains:
        retriever | format_docs  =  search KB, then format results as text
    """
    vectorstore = seed_use_case_kb()
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )


# ---------------------------------------------------------------------------
# CLI — run to seed the knowledge base
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    print(f"\n{'='*50}")
    print("DivAi Knowledge Base Seeder")
    print(f"{'='*50}\n")

    vs = seed_use_case_kb(force_rebuild=force)

    # Demo: test retrieval
    print("\n[Test] Querying: 'SaaS subscription churn billing'")
    results = vs.similarity_search("SaaS subscription churn billing", k=3)
    for i, doc in enumerate(results, 1):
        title_line = [l for l in doc.page_content.split('\n') if 'USE CASE:' in l]
        title = title_line[0].replace('USE CASE:', '').strip() if title_line else "?"
        print(f"  [{i}] {title} (category={doc.metadata.get('category')})")

    print("\n[Test] Querying: 'payment processing fraud detection'")
    results = vs.similarity_search("payment processing fraud detection", k=3)
    for i, doc in enumerate(results, 1):
        title_line = [l for l in doc.page_content.split('\n') if 'USE CASE:' in l]
        title = title_line[0].replace('USE CASE:', '').strip() if title_line else "?"
        print(f"  [{i}] {title} (category={doc.metadata.get('category')})")
