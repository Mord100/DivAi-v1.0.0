"""
DivAi — Supabase Persistence Layer

All Supabase database and Storage operations live here.
The in-memory session_store.py continues to handle live pipeline
state (SSE queues, threading.Event) — that can't be persisted.
This module handles durable storage so data survives restarts.

Two clients:
  get_client()         → anon key, scoped by RLS — DB reads/writes
  get_storage_client() → service role key, bypasses RLS — Storage uploads
"""

import os
import re
from urllib.parse import urlparse
from supabase import create_client, Client

STORAGE_BUCKET = "div-ai-prp"

_client: Client | None = None
_storage_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
        _client = create_client(url, key)
    return _client


def get_storage_client() -> Client:
    global _storage_client
    if _storage_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        _storage_client = create_client(url, key)
    return _storage_client


# Service role client — bypasses RLS for backend-side reads
get_service_client = get_storage_client


def ensure_bucket() -> None:
    try:
        client = get_storage_client()
        existing = [b.name for b in client.storage.list_buckets()]
        if STORAGE_BUCKET not in existing:
            client.storage.create_bucket(STORAGE_BUCKET, options={"public": False})
            print(f"[Supabase] Created storage bucket: {STORAGE_BUCKET}")
    except Exception as e:
        print(f"[Supabase] Bucket setup warning: {e}")


def _normalise_url(url: str) -> str:
    """Strip scheme, www, query params and trailing slash for root_url grouping."""
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        host = re.sub(r"^www\.", "", parsed.netloc or "")
        return host + parsed.path.rstrip("/")
    except Exception:
        return url


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def upsert_user(email: str, name: str | None = None, company: str | None = None,
               user_id: str | None = None) -> str | None:
    """
    Insert or update a user row by email. Returns the user's UUID.

    Never mutates an existing row's primary key — changing it would violate the
    scans FK constraint. For existing users we keep their id and only update
    name/company. For new users we use user_id (Supabase auth UUID) as the id.
    """
    try:
        client = get_service_client()
        email_clean = email.lower().strip()

        existing = client.table("users").select("id").eq("email", email_clean).execute()
        if existing.data:
            # Return existing id — never mutate a row that scans FK-reference
            return existing.data[0]["id"]

        # New user — use Supabase auth UUID as id when available
        payload: dict = {"email": email_clean}
        if user_id:
            payload["id"] = user_id
        if name:    payload["name"]    = name.strip()
        if company: payload["company"] = company.strip()
        res = client.table("users").insert(payload).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        print(f"[Supabase] upsert_user warning: {e}")
        return None


def get_user_by_email(email: str) -> dict | None:
    try:
        res = get_client().table("users").select("*").eq("email", email.lower().strip()).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"[Supabase] get_user_by_email warning: {e}")
        return None


# ---------------------------------------------------------------------------
# Scan row operations
# ---------------------------------------------------------------------------

def upsert_scan(session_id: str, url: str, depth: str, status: str,
                current_stage: str | None = None, error: str | None = None,
                user_id: str | None = None) -> None:
    """Insert or update a scan row."""
    try:
        payload: dict = {
            "id": session_id,
            "url": url,
            "root_url": _normalise_url(url),
            "depth": depth,
            "status": status,
            "current_stage": current_stage,
            "error": error,
        }
        if user_id:
            payload["user_id"] = user_id

        # Detect if there's an existing completed scan for same root_url (re-scan)
        try:
            existing = (
                get_client()
                .table("scans")
                .select("id")
                .eq("root_url", _normalise_url(url))
                .eq("status", "complete")
                .neq("id", session_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if existing.data:
                payload["parent_scan_id"] = existing.data[0]["id"]
        except Exception:
            pass

        get_client().table("scans").upsert(payload).execute()
    except Exception as e:
        print(f"[Supabase] upsert_scan warning: {e}")


def update_scan_status(session_id: str, status: str,
                       current_stage: str | None = None, error: str | None = None) -> None:
    try:
        payload: dict = {"status": status}
        if current_stage is not None:
            payload["current_stage"] = current_stage
        if error is not None:
            payload["error"] = error
        get_client().table("scans").update(payload).eq("id", session_id).execute()
    except Exception as e:
        print(f"[Supabase] update_scan_status warning: {e}")


def update_scan_payment(session_id: str, promo_code: str | None = None,
                        paid: bool = False, amount: float | None = None) -> None:
    """Record payment / promo code outcome on the scan row."""
    try:
        from datetime import datetime, timezone
        payload: dict = {"paid": paid}
        if promo_code:
            payload["promo_code_used"] = promo_code
        if paid:
            payload["payment_amount"] = amount or 0
            payload["payment_at"] = datetime.now(timezone.utc).isoformat()
        get_client().table("scans").update(payload).eq("id", session_id).execute()
    except Exception as e:
        print(f"[Supabase] update_scan_payment warning: {e}")


def update_lead_score(session_id: str, final_state: dict) -> int:
    """
    Compute and persist a lead score (0–100) based on pipeline output signals.

    Scoring:
      Tech stack confidence   → up to 20 pts
      API endpoints detected  → up to 20 pts (2 pts each, max 10)
      Use cases generated     → up to 20 pts (4 pts each, max 5)
      Proposal generated      → 20 pts
      Paid                    → 20 pts (updated later via update_scan_payment)
    """
    try:
        report    = final_state.get("intelligence_report") or {}
        use_cases = final_state.get("use_cases") or []
        proposal  = final_state.get("proposal_paths")

        tech       = report.get("tech_stack") or {}
        confidence = float(tech.get("confidence", 0))
        endpoints  = len(report.get("api_endpoints") or [])

        score = 0
        score += int(confidence * 20)
        score += min(endpoints, 10) * 2
        score += min(len(use_cases), 5) * 4
        if proposal:
            score += 20

        score = min(score, 80)  # 20 pts reserved for payment

        get_client().table("scans").update({"lead_score": score}).eq("id", session_id).execute()
        return score
    except Exception as e:
        print(f"[Supabase] update_lead_score warning: {e}")
        return 0


# ---------------------------------------------------------------------------
# Scan results
# ---------------------------------------------------------------------------

def save_scan_results(session_id: str, final_state: dict) -> None:
    try:
        get_client().table("scan_results").upsert({
            "id": session_id,
            "intelligence_report": final_state.get("intelligence_report"),
            "use_cases": final_state.get("use_cases"),
            "solutions": final_state.get("solutions"),
            "proposal_paths": final_state.get("proposal_paths"),
            "pipeline_log": final_state.get("pipeline_log"),
        }).execute()
    except Exception as e:
        print(f"[Supabase] save_scan_results warning: {e}")


# ---------------------------------------------------------------------------
# Load scan from Supabase (fallback when session not in memory)
# ---------------------------------------------------------------------------

def load_scan_from_supabase(session_id: str) -> dict | None:
    """
    Load a completed scan's full data from Supabase.
    Used as a fallback when the in-memory session_store doesn't have the session
    (e.g. after a server restart on Render free tier).

    Returns a dict with keys: status, intelligence_report, use_cases,
    solutions, proposal_paths, pipeline_log — or None if not found.
    """
    try:
        client = get_service_client()

        # Get scan status from scans table
        scan_res = client.table("scans").select("id, status").eq("id", session_id).execute()
        if not scan_res.data:
            return None

        scan_row = scan_res.data[0]
        status = scan_row.get("status", "unknown")

        # Get full results from scan_results table
        results_res = (
            client.table("scan_results")
            .select("intelligence_report, use_cases, solutions, proposal_paths, pipeline_log")
            .eq("id", session_id)
            .execute()
        )

        if not results_res.data:
            return {"status": status}

        row = results_res.data[0]
        return {
            "status": status,
            "intelligence_report": row.get("intelligence_report"),
            "use_cases": row.get("use_cases"),
            "solutions": row.get("solutions"),
            "proposal_paths": row.get("proposal_paths"),
            "pipeline_log": row.get("pipeline_log"),
        }
    except Exception as e:
        print(f"[Supabase] load_scan_from_supabase warning: {e}")
        return None


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

def track_event(scan_id: str, event_type: str,
                user_id: str | None = None, metadata: dict | None = None) -> None:
    """
    Record a behavioural event against a scan.
    event_type values: report_viewed, proposal_downloaded, use_case_selected,
                       solution_selected, tab_switched, scan_abandoned, payment_attempted
    """
    try:
        payload: dict = {
            "scan_id": scan_id,
            "event_type": event_type,
            "metadata": metadata or {},
        }
        if user_id:
            payload["user_id"] = user_id
        get_client().table("scan_events").insert(payload).execute()

        # If proposal was downloaded, bump lead score by 10
        if event_type == "proposal_downloaded":
            res = get_client().table("scans").select("lead_score").eq("id", scan_id).execute()
            if res.data:
                current = res.data[0]["lead_score"] or 0
                new_score = min(current + 10, 100)
                get_client().table("scans").update({"lead_score": new_score}).eq("id", scan_id).execute()
    except Exception as e:
        print(f"[Supabase] track_event warning: {e}")


# ---------------------------------------------------------------------------
# Proposal file storage
# ---------------------------------------------------------------------------

def upload_proposal(session_id: str, file_path: str) -> str | None:
    if not file_path or not os.path.exists(file_path):
        return None
    try:
        client = get_storage_client()
        filename = os.path.basename(file_path)
        storage_path = f"{session_id}/{filename}"

        with open(file_path, "rb") as f:
            client.storage.from_(STORAGE_BUCKET).upload(
                storage_path, f,
                file_options={
                    "content-type": (
                        "application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document"
                    ),
                    "upsert": "true",
                },
            )

        res = client.storage.from_(STORAGE_BUCKET).create_signed_url(
            storage_path, expires_in=86400
        )
        return res.get("signedURL")
    except Exception as e:
        print(f"[Supabase] upload_proposal warning: {e}")
        return None


def get_download_url(session_id: str, filename: str, expires_in: int = 3600) -> str | None:
    try:
        storage_path = f"{session_id}/{filename}"
        res = get_storage_client().storage.from_(STORAGE_BUCKET).create_signed_url(
            storage_path, expires_in=expires_in
        )
        return res.get("signedURL")
    except Exception as e:
        print(f"[Supabase] get_download_url warning: {e}")
        return None
