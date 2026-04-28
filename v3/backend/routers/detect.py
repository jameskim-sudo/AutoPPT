import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.schemas import DetectResponse, TextLayer, TextBlock
from services.ocr_service import detect_text
from utils.image_utils import get_image_size

router = APIRouter()
WORKSPACE = Path("workspace")


class DetectRequest(BaseModel):
    session_id: str


@router.post("/detect-text", response_model=DetectResponse)
async def detect_text_endpoint(req: DetectRequest):
    session_dir = WORKSPACE / req.session_id
    original_path = session_dir / "original.png"

    if not original_path.exists():
        raise HTTPException(404, "Session not found. Upload an image first.")

    width, height = get_image_size(original_path)

    # Run blocking OCR in a thread pool so the event loop is not blocked
    try:
        loop = asyncio.get_event_loop()
        blocks: list[TextBlock] = await loop.run_in_executor(None, detect_text, original_path)
    except Exception as e:
        raise HTTPException(500, f"OCR failed: {e}")

    text_layer = TextLayer(
        session_id=req.session_id,
        image_width=width,
        image_height=height,
        blocks=blocks,
    )

    tl_path = session_dir / "text_layer.json"
    tl_path.write_text(text_layer.model_dump_json(indent=2), encoding="utf-8")

    return DetectResponse(
        session_id=req.session_id,
        text_layer=text_layer,
        block_count=len(blocks),
    )
