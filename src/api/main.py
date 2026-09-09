"""
DivAi — FastAPI Application Entry Point (Phase 6)

WHAT THIS FILE DOES:
  Creates the FastAPI app, configures middleware, and registers all routes.
  Run with: uvicorn api.main:app --reload --port 8000

CONCEPT: FastAPI App Lifecycle
---------------------------------
A FastAPI app has three phases:
  1. Startup  — runs when the server starts (seed KBs, warm up models)
  2. Request  — handles each HTTP request
  3. Shutdown — runs when server stops (close DB connections, cleanup)

We use @app.on_event("startup") to seed the ChromaDB knowledge bases.
Without this, the first scan would take longer (seeding on first call).

CONCEPT: CORS — Cross-Origin Resource Sharing
-----------------------------------------------
Browsers enforce the "same-origin policy": JavaScript from
https://myapp.com can only call APIs on https://myapp.com.
If our Next.js frontend runs on localhost:3000 and the API on
localhost:8000, they're different "origins" (different ports).

CORS middleware tells the browser: "these origins are allowed to
call this API." Without it, browser requests from the Next.js
frontend would be blocked by the browser itself.

CORSMiddleware parameters:
  allow_origins     = list of allowed origins (["*"] = allow all, dev only)
  allow_credentials = allow cookies/auth headers
  allow_methods     = which HTTP methods are allowed
  allow_headers     = which request headers are allowed

CONCEPT: Router Prefixes
--------------------------
Instead of writing "/api/scan", "/api/stream", "/api/report" as
the full path in every route, we set prefix="/api" on the router.
The router handles relative paths, the prefix is added automatically.
This makes it easy to version the API: prefix="/api/v2" and all
routes update at once.
"""

import sys
import os

# Force UTF-8 output on Windows — prevents charmap codec errors when
# agents print Unicode characters (arrows, emoji, etc.) to the console.
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Make sure imports from src/ work regardless of where uvicorn is started
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import scan, stream, report, interact, download, chat, auth_capture, admin, events, users, regenerate, rerun_solutions


# ---------------------------------------------------------------------------
# Create the FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="DivAi API",
    description=(
        "AI-powered business intelligence platform. "
        "POST a URL → get a full technical proposal in under 5 minutes."
    ),
    version="0.6.0",
    docs_url="/docs",       # Swagger UI at /docs
    redoc_url="/redoc",     # ReDoc UI at /redoc
)


# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
# CONCEPT: In development we allow all origins ("*").
# In production (Phase 7), replace "*" with the exact frontend URL:
#   allow_origins=["https://divai.yourdomain.com"]

# CORS: when allow_credentials=True the browser rejects Access-Control-Allow-Origin: *
# so we must always list explicit origins. Default to both dev ports; set
# ALLOWED_ORIGINS in production to the real frontend URL.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001")
_origins = [o.strip() for o in _raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)


# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------
# CONCEPT: APIRouter lets you split routes across files.
# Each router handles a logical group (scan, stream, report).
# We mount them all under /api prefix here in main.py.

app.include_router(scan.router,      prefix="/api", tags=["Scan"])
app.include_router(stream.router,    prefix="/api", tags=["Stream"])
app.include_router(report.router,    prefix="/api", tags=["Report"])
app.include_router(interact.router,  prefix="/api", tags=["Interact"])
app.include_router(download.router,  prefix="/api", tags=["Download"])
app.include_router(chat.router,        prefix="/api", tags=["Chat"])
app.include_router(auth_capture.router, prefix="/api", tags=["Auth Capture"])
app.include_router(admin.router,       prefix="/api", tags=["Admin"])
app.include_router(events.router,      prefix="/api", tags=["Events"])
app.include_router(users.router,       prefix="/api", tags=["Users"])
app.include_router(regenerate.router,      prefix="/api", tags=["Regenerate"])
app.include_router(rerun_solutions.router, prefix="/api", tags=["Rerun Solutions"])


# ---------------------------------------------------------------------------
# Health check + root
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "service": "DivAi API",
        "version": "0.6.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/api/health")
async def health():
    """
    Health check endpoint.
    Load balancers and monitoring tools call this to verify the service is up.
    Returns 200 if healthy.
    """
    return {"status": "healthy", "service": "divai-api"}


# ---------------------------------------------------------------------------
# Startup: seed knowledge bases
# ---------------------------------------------------------------------------
# CONCEPT: Lifespan Events
# Code here runs once when the server starts.
# We seed the ChromaDB knowledge bases so they're ready for the first scan.
# Without seeding, the first request to use_case_agent or solution_agent
# would trigger the embedding computation (~5 seconds delay).

@app.on_event("startup")
async def startup_event():
    """Warm up the RAG knowledge bases and ensure Supabase Storage bucket exists."""
    import asyncio
    loop = asyncio.get_running_loop()

    def startup_tasks():
        # Seed RAG knowledge bases
        try:
            from rag.knowledge_base import seed_use_case_kb
            from rag.solution_knowledge_base import seed_solution_kb
            seed_use_case_kb(force_rebuild=False)
            seed_solution_kb(force_rebuild=False)
            print("[Startup] Knowledge bases ready.")
        except Exception as e:
            print(f"[Startup] KB seed warning: {e}")

        # Ensure Supabase Storage bucket exists
        try:
            from api.supabase_store import ensure_bucket
            ensure_bucket()
        except Exception as e:
            print(f"[Startup] Supabase bucket warning: {e}")

    await loop.run_in_executor(None, startup_tasks)


# ---------------------------------------------------------------------------
# Entry point: run with uvicorn directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,    # Auto-restart on file changes (development only)
        log_level="info",
    )
