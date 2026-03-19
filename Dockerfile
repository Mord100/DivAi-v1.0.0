# ============================================================
# DivAi Backend — Dockerfile
# ============================================================
# Uses python:3.12-slim as the base. We need extra system libs
# because Playwright drives a real Chromium browser internally.
# ============================================================

FROM python:3.12-slim

# ---------------------------------------------------------------------------
# System dependencies required by Chromium (Playwright's browser)
# ---------------------------------------------------------------------------
# These are C libraries that Chromium links against at runtime.
# Without them, `playwright install chromium` installs fine but the
# browser crashes immediately when launched.
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Set up working directory
# ---------------------------------------------------------------------------
WORKDIR /app

# ---------------------------------------------------------------------------
# Install Python dependencies
# ---------------------------------------------------------------------------
# WHY the two-step install?
# sentence-transformers depends on PyTorch. If we let pip resolve it freely
# it downloads the full CUDA-enabled build (~2.5 GB) even though Railway
# has no GPU. We pre-install the CPU-only build (~800 MB) first; pip then
# sees torch as already satisfied and skips the GPU version.
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Install Playwright's Chromium browser
# ---------------------------------------------------------------------------
# `playwright install chromium` downloads the Chromium binary that
# Playwright controls. We only install Chromium (not Firefox/WebKit)
# to keep the image smaller (~150MB instead of ~600MB for all browsers).
RUN playwright install chromium

# ---------------------------------------------------------------------------
# Copy application source
# ---------------------------------------------------------------------------
COPY src/ ./src/

# ---------------------------------------------------------------------------
# Data directory for ChromaDB persistence
# ---------------------------------------------------------------------------
# ChromaDB stores its SQLite + HNSW index files here.
# On Railway, mount a volume to /app/data so they survive redeploys.
RUN mkdir -p /app/data/chroma

# ---------------------------------------------------------------------------
# Environment defaults
# ---------------------------------------------------------------------------
# PYTHONPATH lets Python find modules in src/ (e.g. "from api.main import app")
ENV PYTHONPATH=/app/src
# Playwright needs this when running as root inside Docker
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# ---------------------------------------------------------------------------
# Expose port + start server
# ---------------------------------------------------------------------------
# Railway injects $PORT automatically — we fall back to 8000 for local Docker.
EXPOSE 8000
CMD ["sh", "-c", "cd /app/src && uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
