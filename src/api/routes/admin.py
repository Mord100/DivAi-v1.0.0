"""
DivAi — Admin Routes

ENDPOINTS:
  GET /api/admin/stats              — summary counts, conversion, top leads
  GET /api/admin/scans              — paginated scan list with lead scores
  GET /api/admin/scans/{id}         — full scan detail with results + events
  GET /api/admin/users              — all identified users with scan counts
  GET /api/admin/users/{id}         — user detail with their scan history
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException, Query
from api.supabase_store import get_client

router = APIRouter()


@router.get("/admin/stats")
async def get_stats():
    try:
        client = get_client()

        scans_res = client.table("scans").select("status, paid, lead_score").execute()
        rows = scans_res.data or []

        total    = len(rows)
        by_status: dict[str, int] = {}
        paid     = 0
        total_score = 0

        for row in rows:
            s = row["status"]
            by_status[s] = by_status.get(s, 0) + 1
            if row.get("paid"):
                paid += 1
            total_score += row.get("lead_score") or 0

        complete = by_status.get("complete", 0)

        users_res  = client.table("users").select("id", count="exact").execute()
        events_res = client.table("scan_events").select("event_type").execute()
        events     = events_res.data or []
        downloads  = sum(1 for e in events if e["event_type"] == "proposal_downloaded")

        top_leads_res = (
            client.table("scans")
            .select("id, url, lead_score, status, created_at, users(email, name, company)")
            .eq("status", "complete")
            .order("lead_score", desc=True)
            .limit(5)
            .execute()
        )

        return {
            "total_scans":       total,
            "by_status":         by_status,
            "completion_rate":   round(complete / total * 100, 1) if total else 0,
            "total_users":       users_res.count or 0,
            "paid_scans":        paid,
            "conversion_rate":   round(paid / complete * 100, 1) if complete else 0,
            "proposal_downloads": downloads,
            "avg_lead_score":    round(total_score / total, 1) if total else 0,
            "top_leads":         top_leads_res.data or [],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/scans")
async def list_scans(
    page: int      = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
):
    try:
        client = get_client()
        offset = (page - 1) * page_size

        query = (
            client.table("scans")
            .select(
                "id, url, depth, status, current_stage, error, "
                "lead_score, paid, promo_code_used, root_url, parent_scan_id, "
                "created_at, updated_at, users(email, name, company)"
            )
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
        )
        if status:
            query = query.eq("status", status)

        res = query.execute()
        return {"page": page, "page_size": page_size, "scans": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/scans/{scan_id}")
async def get_scan_detail(scan_id: str):
    try:
        client = get_client()

        scan_res = (
            client.table("scans")
            .select("*, users(id, email, name, company)")
            .eq("id", scan_id)
            .single()
            .execute()
        )
        if not scan_res.data:
            raise HTTPException(status_code=404, detail="Scan not found")

        results_res = (
            client.table("scan_results")
            .select("intelligence_report, use_cases, solutions, proposal_paths, pipeline_log, created_at")
            .eq("id", scan_id)
            .execute()
        )

        events_res = (
            client.table("scan_events")
            .select("event_type, metadata, created_at")
            .eq("scan_id", scan_id)
            .order("created_at")
            .execute()
        )

        # Fetch sibling scans (same root_url)
        root_url = scan_res.data.get("root_url")
        siblings: list = []
        if root_url:
            sib_res = (
                client.table("scans")
                .select("id, status, lead_score, created_at")
                .eq("root_url", root_url)
                .neq("id", scan_id)
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )
            siblings = sib_res.data or []

        return {
            "scan":     scan_res.data,
            "results":  results_res.data[0] if results_res.data else None,
            "events":   events_res.data or [],
            "siblings": siblings,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/users")
async def list_users(
    page: int      = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    try:
        client = get_client()
        offset = (page - 1) * page_size

        res = (
            client.table("users")
            .select("id, email, name, company, created_at")
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        users = res.data or []

        # Attach scan counts and max lead score per user
        for user in users:
            scan_res = (
                client.table("scans")
                .select("id, status, lead_score, paid")
                .eq("user_id", user["id"])
                .execute()
            )
            scans = scan_res.data or []
            user["scan_count"]   = len(scans)
            user["paid_count"]   = sum(1 for s in scans if s.get("paid"))
            user["top_score"]    = max((s.get("lead_score") or 0 for s in scans), default=0)
            user["completed"]    = sum(1 for s in scans if s.get("status") == "complete")

        return {"page": page, "page_size": page_size, "users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/users/{user_id}")
async def get_user_detail(user_id: str):
    try:
        client = get_client()

        user_res = (
            client.table("users").select("*").eq("id", user_id).single().execute()
        )
        if not user_res.data:
            raise HTTPException(status_code=404, detail="User not found")

        scans_res = (
            client.table("scans")
            .select("id, url, status, lead_score, paid, promo_code_used, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        events_res = (
            client.table("scan_events")
            .select("scan_id, event_type, metadata, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )

        return {
            "user":   user_res.data,
            "scans":  scans_res.data or [],
            "events": events_res.data or [],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
