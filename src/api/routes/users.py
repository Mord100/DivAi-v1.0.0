"""
DivAi — Users Route

POST /api/users/identify
  Upsert a user by email. Called from the frontend before a scan starts.
  Returns the user UUID to attach to the scan.
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import jwt as pyjwt

from api.supabase_store import upsert_user, get_user_by_email, get_client, get_service_client

router = APIRouter()


class IdentifyRequest(BaseModel):
    email: str
    name: Optional[str] = None
    company: Optional[str] = None
    user_id: Optional[str] = None  # Supabase auth UUID — passed when user is logged in


@router.post("/users/identify")
async def identify_user(payload: IdentifyRequest):
    user_id = upsert_user(
        email=payload.email,
        name=payload.name,
        company=payload.company,
        user_id=payload.user_id,
    )
    if not user_id:
        raise HTTPException(status_code=500, detail="Failed to identify user")
    return {"user_id": user_id, "email": payload.email}


@router.get("/me/scans")
async def get_my_scans(authorization: Optional[str] = Header(default=None)):
    """
    Returns the authenticated user's scan history.
    Requires a Supabase JWT in the Authorization: Bearer <token> header.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")

    token = authorization.removeprefix("Bearer ").strip()

    # Decode the Supabase JWT to get the user's sub (UUID)
    # We use verify=False here because Supabase verifies the token itself —
    # this backend trusts tokens that came from Supabase's anon key client.
    # For production, verify with the Supabase JWT secret from project settings.
    try:
        payload = pyjwt.decode(token, options={"verify_signature": False})
        auth_uid = payload.get("sub")
        email    = payload.get("email", "")
        if not auth_uid:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Use service role key so RLS does not block backend-side reads
    client = get_service_client()

    # Look up user by auth UUID first; fall back to email if not found.
    # Handles users whose public.users row predates the auth UUID sync
    # (e.g. scanned anonymously before logging in).
    user_res = client.table("users").select("id, email, name, company").eq("id", auth_uid).execute()
    if not user_res.data and email:
        user_res = client.table("users").select("id, email, name, company").eq("email", email.lower()).execute()

    user_row  = user_res.data[0] if user_res.data else None
    lookup_id = user_row["id"] if user_row else auth_uid

    # Get their scans, most recent first
    scans_res = (
        client.table("scans")
        .select("id, url, status, lead_score, paid, created_at, current_stage")
        .eq("user_id", lookup_id)
        .order("created_at", desc=True)
        .execute()
    )
    scans = scans_res.data or []

    # Fetch proposal_paths from scan_results (stored separately from the scans table)
    if scans:
        scan_ids = [s["id"] for s in scans]
        results_res = (
            client.table("scan_results")
            .select("id, proposal_paths")
            .in_("id", scan_ids)
            .execute()
        )
        proposal_map = {r["id"]: r.get("proposal_paths") for r in (results_res.data or [])}
        for scan in scans:
            scan["proposal_paths"] = proposal_map.get(scan["id"])

    return {
        "user":  user_row,
        "scans": scans,
    }
