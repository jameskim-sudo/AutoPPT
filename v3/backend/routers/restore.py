from pathlib import Path

from fastapi import APIRouter, HTTPException

from models.schemas import RestoreResponse, UpdateBlocksRequest
from services.restore_service import restore_background

router = APIRouter()
WORKSPACE = Path("workspace")


@router.post("/restore-background", response_model=RestoreResponse)
async def restore_background_endpoint(req: UpdateBlocksRequest):
    session_dir = WORKSPACE / req.session_id

    if not (session_dir / "original.png").exists():
        raise HTTPException(404, "Session not found.")
    if not (session_dir / "final_remove_mask.png").exists():
        raise HTTPException(400, "Run /api/create-masks first.")

    restore_background(session_dir, req.blocks)

    return RestoreResponse(
        session_id=req.session_id,
        restored_background_url=f"/static/{req.session_id}/restored_background.png",
        blocks=req.blocks,
    )
