from pathlib import Path

from fastapi import APIRouter, HTTPException

from models.schemas import RemoveResponse, UpdateBlocksRequest
from services.restore_service import remove_text

router = APIRouter()
WORKSPACE = Path("workspace")


@router.post("/remove-text", response_model=RemoveResponse)
async def remove_text_endpoint(req: UpdateBlocksRequest):
    session_dir = WORKSPACE / req.session_id

    if not (session_dir / "original.png").exists():
        raise HTTPException(404, "Session not found.")
    if not (session_dir / "final_remove_mask.png").exists():
        raise HTTPException(400, "Run /api/create-masks first.")

    remove_text(session_dir, req.blocks)

    return RemoveResponse(
        session_id=req.session_id,
        clean_background_url=f"/static/{req.session_id}/clean_background.png",
        blocks=req.blocks,
    )
