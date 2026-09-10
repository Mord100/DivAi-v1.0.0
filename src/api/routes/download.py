"""
DivAi — Download Route

GET /api/download/{session_id}
  Serves the generated .docx proposal file.

CONCEPT: Supabase Storage Signed URLs vs FileResponse
--------------------------------------------------------
Previously we served the .docx directly from local disk using FileResponse.
That breaks on Railway because the filesystem is ephemeral — files disappear
on every redeploy.

Now we upload the file to Supabase Storage when the pipeline completes and
redirect the client to a signed URL. The file lives in Supabase permanently;
our server just issues the redirect.

CONCEPT: RedirectResponse (303 See Other)
------------------------------------------
Instead of streaming the file bytes through our API server, we tell the client
"go fetch it from this URL instead." This is faster (no double transfer) and
means our server doesn't hold the file in memory at all.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from api.session_store import get_session

router = APIRouter()


@router.get("/download/{session_id}")
async def download_proposal(session_id: str):
    """
    Serve the .docx proposal for download.

    Priority:
      1. Supabase Storage signed URL (survives restarts, preferred in prod)
      2. Local disk FileResponse (fallback for local dev before upload completes)
    """
    paths: dict = {}

    session = get_session(session_id)
    if session:
        if not session.final_state:
            raise HTTPException(status_code=202, detail="Pipeline not complete yet")
        paths = session.final_state.get("proposal_paths") or {}
    else:
        # Fall back to Supabase if session not in memory
        from api.supabase_store import load_scan_from_supabase
        data = load_scan_from_supabase(session_id)
        if not data:
            raise HTTPException(status_code=404, detail="Session not found")
        paths = data.get("proposal_paths") or {}

    # ── Option 1: redirect to Supabase Storage signed URL ────────────────
    signed_url = paths.get("signed_url")
    if signed_url:
        return RedirectResponse(url=signed_url, status_code=303)

    # ── Option 2: fall back to local disk (dev / upload not yet complete) ─
    docx_path = paths.get("docx")
    if not docx_path:
        raise HTTPException(status_code=404, detail="No proposal file in this session")

    if not os.path.exists(docx_path):
        raise HTTPException(
            status_code=404,
            detail=f"Proposal file not found on disk: {docx_path}",
        )

    filename = os.path.basename(docx_path)
    return FileResponse(
        path=docx_path,
        filename=filename,
        media_type=(
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        ),
    )
