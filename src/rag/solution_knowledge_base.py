"""
DivAi — Solution Blueprint Knowledge Base (Phase 3)

WHAT THIS FILE DOES:
  Seeds ChromaDB with solution blueprints — the agency's catalog of
  proven technical solutions. The Solution Agent queries this KB to
  match selected use cases to concrete, deliverable solutions.

CONCEPT: Two Separate Knowledge Bases
---------------------------------------
We use two ChromaDB collections, not one:

  use_case_kb          → "what problems can we solve?" (discovery layer)
  solution_blueprint_kb → "how do we solve them?"      (specification layer)

Keeping them separate means:
  - Sales/BD team can add use case templates without touching tech specs
  - Engineering team can update solution blueprints without touching BD content
  - We can swap the solution KB per client vertical (enterprise vs startup)
  - Each KB can have different chunk sizes and retrieval strategies

CONCEPT: Richer Metadata for Filtered Retrieval
--------------------------------------------------
Solution blueprints have richer metadata than use case templates.
This enables filtered retrieval:
  "find High-value, Low-effort solutions in the AI/ML category"
  "find all solutions that use Python + LangChain"
These filters are applied AT the vector search level — fast and efficient.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from rag.embeddings import get_embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "../../data/chroma")


# ---------------------------------------------------------------------------
# Solution Blueprint Library
# ---------------------------------------------------------------------------
# Each blueprint answers: given this use case, here is our solution package.
# Fields:
#   SOLUTION:      What we deliver (product name / title)
#   MATCHES:       Use cases this blueprint covers
#   ARCHITECTURE:  High-level system design
#   TECH STACK:    Specific technologies used
#   PHASES:        Delivery breakdown
#   TIMELINE:      Realistic duration estimate
#   EFFORT:        Low / Medium / High (team-weeks)
#   VALUE SCORE:   Expected ROI/impact for the client
#   RISKS:         Known technical/business risks
#   PREREQUISITES: What the client needs to provide

SOLUTION_BLUEPRINTS = [

    # ── AI / LLM SOLUTIONS ──────────────────────────────────────────────────

    Document(
        page_content="""
SOLUTION: AI Customer Support Agent (RAG-Powered)
MATCHES: AI-Powered Support Chatbot, Customer Support Automation,
  Help Desk Deflection, Tier-1 Support Automation.
ARCHITECTURE: RAG pipeline over client's help docs + ticket history.
  Claude API for conversational reasoning. Streaming responses via SSE.
  Escalation logic with confidence thresholds. Human handoff protocol.
  Admin dashboard for monitoring deflection rates and failed queries.
TECH STACK:
  - Backend: Python, FastAPI, LangChain, LangGraph
  - LLM: Claude claude-sonnet-4-6 (claude-sonnet-4-6)
  - Vector DB: ChromaDB (dev) → Pinecone (prod)
  - Embeddings: Anthropic Embeddings API
  - Frontend: React/Next.js chat widget, embeddable via script tag
  - Infra: AWS Lambda + API Gateway (serverless, scales to 0)
PHASES:
  Phase 1 (Week 1-2): Knowledge base ingestion pipeline, RAG setup
  Phase 2 (Week 3-4): Conversational agent, escalation logic, API
  Phase 3 (Week 5-6): Frontend widget, admin dashboard, monitoring
TIMELINE: 6 weeks
EFFORT: Medium (2 engineers, 6 weeks)
VALUE SCORE: Very High — 40-60% ticket deflection, measurable in week 1
RISKS:
  - Knowledge base quality determines answer quality (garbage in = garbage out)
  - Needs ongoing KB maintenance as product evolves
  - Edge cases requiring human judgment must be handled gracefully
PREREQUISITES: Existing help docs or knowledge base, chat widget integration point.
""",
        metadata={"category": "AI/LLM", "effort": "Medium",
                  "value": "Very High", "timeline": "6 weeks",
                  "id": "sol_ai_support_agent"}
    ),

    Document(
        page_content="""
SOLUTION: Document Intelligence & Data Extraction Pipeline
MATCHES: Document Intelligence, Invoice Processing, Contract Analysis,
  Data Extraction, OCR Automation, Manual Data Entry Elimination.
ARCHITECTURE: Multi-stage pipeline: upload → OCR (AWS Textract or
  pytesseract) → LLM extraction (Claude with structured output) →
  Pydantic validation → human review UI → downstream system integration.
  Supports PDF, Word, images. Handles multiple document types with
  separate extraction schemas per type.
TECH STACK:
  - Pipeline: Python, LangChain, Pydantic, Celery (async jobs)
  - OCR: AWS Textract (primary), pytesseract (fallback)
  - LLM: Claude API with structured output (tool use)
  - Storage: S3 for raw docs, PostgreSQL for extracted data
  - Frontend: React review/correction UI with field highlighting
  - Infra: AWS ECS for pipeline workers, S3 trigger for auto-processing
PHASES:
  Phase 1 (Week 1-2): Pipeline skeleton, OCR integration, single doc type
  Phase 2 (Week 3): Multi-doc-type schemas, validation layer
  Phase 3 (Week 4-5): Review UI, correction workflow, downstream integrations
TIMELINE: 5 weeks
EFFORT: Medium (2 engineers, 5 weeks)
VALUE SCORE: High — eliminates 80-90% of manual data entry, ROI in weeks
RISKS:
  - Poor scan quality degrades OCR accuracy
  - Complex tables or multi-column layouts need custom parsing logic
  - Client needs to validate extraction accuracy during UAT
PREREQUISITES: Sample documents (min 20-50 examples per type), target data schema.
""",
        metadata={"category": "AI/LLM", "effort": "Medium",
                  "value": "High", "timeline": "5 weeks",
                  "id": "sol_ai_document_extraction"}
    ),

    Document(
        page_content="""
SOLUTION: AI Content Generation & Personalisation Engine
MATCHES: Personalised Content Generation, Email Personalisation,
  Product Description Generation, Marketing Copy at Scale.
ARCHITECTURE: Template-driven generation pipeline. Segment definition
  layer → variable injection → Claude generation → human approval queue
  → CRM/email platform push. Batch processing for large sends.
  A/B testing framework built in.
TECH STACK:
  - Backend: Python, FastAPI, LangChain (LCEL chains)
  - LLM: Claude claude-sonnet-4-6 with prompt templates
  - Queue: Redis + Celery for batch generation jobs
  - Storage: PostgreSQL for templates and generated content
  - Integrations: Klaviyo, Mailchimp, HubSpot, Salesforce (via API)
  - Frontend: React approval dashboard with diff view
PHASES:
  Phase 1 (Week 1): Template system, Claude integration, single channel
  Phase 2 (Week 2-3): Batch processing, approval workflow, multi-channel
  Phase 3 (Week 4): A/B testing, analytics, CRM integration
TIMELINE: 4 weeks
EFFORT: Low (1-2 engineers, 4 weeks)
VALUE SCORE: High — 6x personalised content performance vs generic
RISKS:
  - Tone/brand voice consistency requires prompt engineering iteration
  - Legal review required for regulated industries (finance, health)
  - Human approval step adds latency to time-sensitive campaigns
PREREQUISITES: Brand guidelines, existing content examples, CRM/email platform API access.
""",
        metadata={"category": "AI/LLM", "effort": "Low",
                  "value": "High", "timeline": "4 weeks",
                  "id": "sol_ai_content_engine"}
    ),

    # ── SAAS / PLATFORM ─────────────────────────────────────────────────────

    Document(
        page_content="""
SOLUTION: Developer Portal — API Docs, Sandbox & Key Management
MATCHES: Developer Portal, API Documentation, Developer Experience,
  Public API Platform, SDK Distribution, Developer Onboarding.
ARCHITECTURE: OpenAPI spec auto-generation from existing API.
  Interactive docs with live request sandbox. API key management console
  (create, rotate, revoke, rate-limit per key). Usage analytics per key.
  Multi-language code examples (Python, JS, curl, PHP, Ruby).
  Webhooks testing console.
TECH STACK:
  - Docs: Next.js 14 + MDX, auto-generated from OpenAPI/Swagger spec
  - Interactive sandbox: Stoplight Elements or custom React
  - API key service: FastAPI + PostgreSQL + Redis (rate limiting)
  - Analytics: ClickHouse or PostgreSQL for usage metrics
  - Auth: JWT for developer accounts, API key hashing (bcrypt)
  - Deployment: Vercel (docs) + AWS ECS (key management API)
PHASES:
  Phase 1 (Week 1-2): OpenAPI spec, static docs site, code examples
  Phase 2 (Week 3-4): Interactive sandbox, API key console
  Phase 3 (Week 5): Usage analytics, webhook tester, search
TIMELINE: 5 weeks
EFFORT: Medium (2 engineers, 5 weeks)
VALUE SCORE: High — reduces developer onboarding from days to hours
RISKS:
  - OpenAPI spec must be kept in sync with actual API (schema drift)
  - Sandbox needs isolated environment (no production data exposure)
  - Rate limiting strategy needs careful design for fair use
PREREQUISITES: Existing API (REST), ability to generate OpenAPI spec, developer sign-up flow.
""",
        metadata={"category": "Platform", "effort": "Medium",
                  "value": "High", "timeline": "5 weeks",
                  "id": "sol_platform_developer_portal"}
    ),

    Document(
        page_content="""
SOLUTION: Self-Serve Analytics & Embedded BI Dashboard
MATCHES: Self-Serve Analytics, Embedded Reporting, Customer Dashboard,
  Data Visualisation, Business Intelligence, Metrics Dashboard.
ARCHITECTURE: Multi-tenant analytics layer. Row-level security ensures
  each customer only sees their own data. Pre-built chart library.
  Custom query builder for power users. Scheduled report delivery.
  Export to CSV/PDF. Embeddable via iframe or React component.
TECH STACK:
  - Backend: Python FastAPI, SQLAlchemy, PostgreSQL
  - Analytics engine: Apache Superset (open source) or custom React + Recharts
  - Row-level security: PostgreSQL RLS policies + JWT claims
  - Cache: Redis for expensive query results (TTL-based invalidation)
  - Frontend: React, Recharts/Victory charts, date-range picker
  - Export: python-pptx (slides), WeasyPrint (PDF), pandas (CSV)
PHASES:
  Phase 1 (Week 1-2): Data API, RLS setup, core metric charts
  Phase 2 (Week 3-4): Chart builder, filtering, time range controls
  Phase 3 (Week 5): Scheduled reports, export, embed widget
TIMELINE: 5 weeks
EFFORT: Medium (2 engineers, 5 weeks)
VALUE SCORE: High — increases product retention by 15-25%
RISKS:
  - Complex queries can cause performance issues at scale (needs query optimiser)
  - Row-level security requires careful testing (data leakage risk)
  - Schema changes in the main DB must be reflected in analytics layer
PREREQUISITES: Existing data in PostgreSQL or accessible via API, defined KPIs.
""",
        metadata={"category": "Platform", "effort": "Medium",
                  "value": "High", "timeline": "5 weeks",
                  "id": "sol_platform_analytics"}
    ),

    Document(
        page_content="""
SOLUTION: Internal Admin Panel & Operations Dashboard
MATCHES: Internal Admin Panel, Ops Dashboard, Back-Office Tooling,
  Customer Success Tooling, Manual Admin Task Automation.
ARCHITECTURE: Role-based internal web app. CRUD operations over core
  data models with audit logging. Feature flag management. Bulk actions.
  Customer impersonation (for support). Activity timeline per entity.
  Search across all entities. Exportable reports.
TECH STACK:
  - Frontend: React Admin framework or Retool (low-code for speed)
    Custom React if complex UI requirements
  - Backend: FastAPI + SQLAlchemy (thin API layer over existing DB)
  - Auth: SSO via Google Workspace (internal only), RBAC middleware
  - Audit log: append-only PostgreSQL table with user + action + timestamp
  - Feature flags: LaunchDarkly or custom flag service
  - Deployment: Internal VPN-gated, AWS ECS or Fly.io
PHASES:
  Phase 1 (Week 1-2): Core entity CRUD, user management, auth
  Phase 2 (Week 3): Bulk actions, search, audit log, feature flags
  Phase 3 (Week 4): Reporting, impersonation, custom workflows
TIMELINE: 4 weeks
EFFORT: Low (1-2 engineers, 4 weeks)
VALUE SCORE: High — frees 80% of engineering time on one-off admin requests
RISKS:
  - Scope creep — internal tools grow without limit if not controlled
  - Impersonation feature needs careful access control and audit logging
  - Must keep in sync with main app DB schema as it evolves
PREREQUISITES: Existing database schema, list of most common admin tasks/pain points.
""",
        metadata={"category": "Platform", "effort": "Low",
                  "value": "High", "timeline": "4 weeks",
                  "id": "sol_platform_admin_panel"}
    ),

    # ── ML / DATA ────────────────────────────────────────────────────────────

    Document(
        page_content="""
SOLUTION: Churn Prediction & Automated Retention System
MATCHES: Subscription Churn Prediction, Customer Retention Engine,
  SaaS Churn Reduction, Revenue Retention, Lifecycle Marketing.
ARCHITECTURE: ML pipeline: feature engineering from product usage events
  → XGBoost classification model → churn probability score per user
  → score updated daily → risk segments → automated playbook triggers
  (in-app message, email, CSM alert, discount offer based on risk level).
  Dashboard for CSM team showing at-risk accounts.
TECH STACK:
  - ML: Python, scikit-learn / XGBoost, pandas, feature store (Redis)
  - Pipeline: Airflow (daily retraining), MLflow (experiment tracking)
  - Scoring API: FastAPI, real-time score endpoint
  - Integrations: Intercom (in-app), Klaviyo (email), Salesforce (CSM)
  - Dashboard: React + Recharts, sortable risk list
  - Infra: AWS SageMaker (model hosting) or ECS + S3 for models
PHASES:
  Phase 1 (Week 1-2): Feature engineering, EDA, baseline model
  Phase 2 (Week 3-4): Model tuning, scoring API, daily pipeline
  Phase 3 (Week 5-6): Retention playbooks, integrations, CSM dashboard
TIMELINE: 6 weeks
EFFORT: High (2-3 engineers, 6 weeks)
VALUE SCORE: Very High — 1% churn reduction = ~1% ARR recovered
RISKS:
  - Needs minimum 6-12 months of historical churn data to train well
  - Model accuracy degrades as product evolves (needs quarterly retraining)
  - Playbook design requires input from CS/growth team
PREREQUISITES: 12+ months user activity data, churn labels, CRM/email platform access.
""",
        metadata={"category": "ML/Data", "effort": "High",
                  "value": "Very High", "timeline": "6 weeks",
                  "id": "sol_ml_churn_prediction"}
    ),

    Document(
        page_content="""
SOLUTION: Real-Time Fraud Detection & Risk Scoring API
MATCHES: Payment Fraud Detection, Transaction Risk Scoring,
  Chargeback Reduction, Financial Risk Management.
ARCHITECTURE: Real-time scoring API called pre-transaction. Feature
  engineering from: device fingerprint, IP geolocation, transaction
  velocity, account age, payment method history. Gradient boosting
  model scores 0-100. Rules engine overlay for known fraud patterns.
  Case management UI for manual review queue.
TECH STACK:
  - ML: Python, XGBoost, feature engineering pipeline, Redis feature store
  - API: FastAPI, <50ms p99 latency target, async scoring
  - Rules engine: Custom Python rule DSL, hot-reloadable without deploy
  - Case management: React, queue management, analyst workflow
  - Monitoring: Grafana dashboard, alert on score distribution shifts
  - Infra: AWS ECS (auto-scaling), ElastiCache (feature store), RDS
PHASES:
  Phase 1 (Week 1-2): Feature engineering, model training, baseline API
  Phase 2 (Week 3-4): Rules engine, real-time integration, latency optimisation
  Phase 3 (Week 5-6): Case management UI, monitoring, feedback loop
TIMELINE: 6 weeks
EFFORT: High (2-3 engineers, 6 weeks)
VALUE SCORE: Very High — typically saves 0.5-1.5% of GMV in fraud losses
RISKS:
  - High false positive rate damages UX (legitimate transactions declined)
  - Fraudsters adapt — model needs ongoing updates
  - Regulatory requirements vary by geography (PCI DSS, PSD2)
PREREQUISITES: 6+ months transaction history with fraud labels, payment API access.
""",
        metadata={"category": "ML/Data", "effort": "High",
                  "value": "Very High", "timeline": "6 weeks",
                  "id": "sol_ml_fraud_detection"}
    ),

    # ── INFRASTRUCTURE ───────────────────────────────────────────────────────

    Document(
        page_content="""
SOLUTION: CI/CD Pipeline & DevOps Automation
MATCHES: CI/CD Pipeline, DevOps Automation, Deployment Automation,
  Developer Workflow, Infrastructure as Code, Release Engineering.
ARCHITECTURE: GitHub Actions workflows: lint → test → build Docker image
  → push to ECR → deploy to staging → smoke tests → manual approval gate
  → deploy to production. Rollback automation. Slack notifications.
  Infrastructure as code with Terraform. Secrets via AWS Secrets Manager.
TECH STACK:
  - CI/CD: GitHub Actions (primary) or GitLab CI
  - Container: Docker, AWS ECR (registry), AWS ECS Fargate (runtime)
  - IaC: Terraform, remote state in S3 + DynamoDB locking
  - Secrets: AWS Secrets Manager, injected at runtime
  - Monitoring: AWS CloudWatch + PagerDuty for on-call
  - Notifications: Slack webhooks for deploy status
PHASES:
  Phase 1 (Week 1): Dockerise application, ECR setup, basic CI pipeline
  Phase 2 (Week 2): CD pipeline, staging environment, smoke tests
  Phase 3 (Week 3): Production pipeline, approval gates, rollback, IaC
TIMELINE: 3 weeks
EFFORT: Low (1 engineer, 3 weeks)
VALUE SCORE: High — enables multiple daily deploys safely, eliminates manual errors
RISKS:
  - Existing test coverage must be adequate for safe automated deploys
  - Environment parity between staging and production is critical
  - Secrets rotation strategy needed from day 1
PREREQUISITES: Existing application in Git repo, AWS account, basic test suite.
""",
        metadata={"category": "Infrastructure", "effort": "Low",
                  "value": "High", "timeline": "3 weeks",
                  "id": "sol_infra_cicd"}
    ),

    Document(
        page_content="""
SOLUTION: Observability Platform — Monitoring, Alerting & Tracing
MATCHES: Monitoring Platform, Observability, Error Tracking,
  Performance Monitoring, Incident Management, SRE Tooling.
ARCHITECTURE: Three pillars of observability: metrics (Prometheus +
  Grafana), logs (ELK stack or CloudWatch Logs Insights), traces
  (OpenTelemetry + Jaeger or AWS X-Ray). PagerDuty for on-call routing.
  Custom business metric alerts (revenue anomalies, error rate spikes).
  Runbook system linked to each alert.
TECH STACK:
  - Metrics: Prometheus (scraping), Grafana (dashboards + alerts)
  - Logs: CloudWatch Logs or self-hosted ELK (Elasticsearch + Kibana)
  - Tracing: OpenTelemetry instrumentation, Jaeger or AWS X-Ray
  - Alerts: PagerDuty or OpsGenie for on-call escalation
  - Error tracking: Sentry (exceptions with full stack traces)
  - Deployment: Helm charts on Kubernetes or Docker Compose
PHASES:
  Phase 1 (Week 1-2): Prometheus + Grafana, core service dashboards
  Phase 2 (Week 3): Log aggregation, error tracking, basic alerts
  Phase 3 (Week 4): Distributed tracing, on-call runbooks, business KPIs
TIMELINE: 4 weeks
EFFORT: Medium (1-2 engineers, 4 weeks)
VALUE SCORE: High — reduces MTTD from hours to minutes
RISKS:
  - High cardinality metrics can cause storage issues (needs label discipline)
  - Alert fatigue if thresholds not properly calibrated
  - OpenTelemetry instrumentation requires code changes in every service
PREREQUISITES: Production application, AWS or Kubernetes environment.
""",
        metadata={"category": "Infrastructure", "effort": "Medium",
                  "value": "High", "timeline": "4 weeks",
                  "id": "sol_infra_observability"}
    ),
]


# ---------------------------------------------------------------------------
# Seeding function
# ---------------------------------------------------------------------------

def seed_solution_kb(force_rebuild: bool = False) -> Chroma:
    """Seed ChromaDB with solution blueprints."""
    print("[KB] Loading embedding model for solution_blueprint_kb...")

    embeddings = get_embeddings()

    collection_name = "solution_blueprint_kb"
    persist_dir = os.path.abspath(CHROMA_DIR)

    if not force_rebuild:
        try:
            existing = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=persist_dir,
            )
            count = existing._collection.count()
            if count > 0:
                print(f"[KB] Loaded existing solution_blueprint_kb ({count} chunks)")
                return existing
        except Exception:
            pass

    print(f"[KB] Building solution_blueprint_kb with {len(SOLUTION_BLUEPRINTS)} blueprints...")

    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=60)
    chunks = splitter.split_documents(SOLUTION_BLUEPRINTS)
    print(f"[KB] Split into {len(chunks)} chunks")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=persist_dir,
    )

    print(f"[KB] solution_blueprint_kb seeded with {vectorstore._collection.count()} vectors")
    return vectorstore


def get_solution_retriever(k: int = 4):
    """Get a LangChain retriever for the solution blueprint knowledge base."""
    vectorstore = seed_solution_kb()
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv

    print(f"\n{'='*50}")
    print("DivAi Solution KB Seeder")
    print(f"{'='*50}\n")

    vs = seed_solution_kb(force_rebuild=force)

    print("\n[Test] Query: 'developer portal API documentation sandbox'")
    results = vs.similarity_search("developer portal API documentation sandbox", k=3)
    for i, doc in enumerate(results, 1):
        title = [l for l in doc.page_content.split('\n') if 'SOLUTION:' in l]
        print(f"  [{i}] {title[0].replace('SOLUTION:', '').strip() if title else '?'}")

    print("\n[Test] Query: 'churn prediction subscription machine learning'")
    results = vs.similarity_search("churn prediction subscription machine learning", k=3)
    for i, doc in enumerate(results, 1):
        title = [l for l in doc.page_content.split('\n') if 'SOLUTION:' in l]
        print(f"  [{i}] {title[0].replace('SOLUTION:', '').strip() if title else '?'}")
