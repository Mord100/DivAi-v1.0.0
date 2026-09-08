"""
DivAi — Events Route

POST /api/events
  Records a behavioural event from the frontend.
  Used to track: report_viewed, proposal_downloaded, tab_switched,
                 use_case_selected, solution_selected, scan_abandoned,
                 payment_attempted.
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from api.supabase_store import track_event

router = APIRouter()


class EventPayload(BaseModel):
    scan_id: str
    event_type: str
    user_id: Optional[str] = None
    metadata: Optional[dict] = {}


@router.post("/events")
async def post_event(payload: EventPayload):
    track_event(
        scan_id=payload.scan_id,
        event_type=payload.event_type,
        user_id=payload.user_id,
        metadata=payload.metadata or {},
    )
    return {"ok": True}
