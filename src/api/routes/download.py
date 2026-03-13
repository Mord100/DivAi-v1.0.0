"""
DivAi — Download Route

GET /api/download/{session_id}
  Serves the generated .docx proposal file.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.session_store import get_session

router = APIRouter()


@router.get("/download/{session_id}")
async def download_proposal(session_id: str):
    """
    Serve the .docx proposal file for download.

    CONCEPT: FileResponse
    FastAPI's FileResponse streams a file from disk to the client.
    It sets the correct Content-Type and Content-Disposition headers
    so the browser saves it as a file rather than displaying it.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.final_state:
        raise HTTPException(status_code=202, detail="Pipeline not complete yet")

    paths = session.final_state.get("proposal_paths") or {}
    docx_path = paths.get("docx")

    if not docx_path:
        raise HTTPException(status_code=404, detail="No proposal file in this session")

    if not os.path.exists(docx_path):
        raise HTTPException(
            status_code=404,
            detail=f"Proposal file not found on disk: {docx_path}"
        )

    filename = os.path.basename(docx_path)
    return FileResponse(
        path=docx_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
