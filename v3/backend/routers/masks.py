import cv2
from pathlib import Path

from fastapi import APIRouter, HTTPException

from models.schemas import MaskResponse, CreateMasksRequest
from services.mask_service import (
    create_text_mask,
    create_protection_mask,
    create_final_remove_mask,
    compute_risk_score,
)
from utils.image_utils import get_image_size, read_image

router = APIRouter()
WORKSPACE = Path("workspace")


@router.post("/create-masks", response_model=MaskResponse)
async def create_masks(req: CreateMasksRequest):
    session_dir = WORKSPACE / req.session_id
    original_path = session_dir / "original.png"

    if not original_path.exists():
        raise HTTPException(404, "Session not found.")

    width, height = get_image_size(original_path)
    img = read_image(original_path)

    text_mask = create_text_mask(original_path, req.blocks, (height, width))
    protection_mask = create_protection_mask(original_path, (height, width))
    final_mask = create_final_remove_mask(
        text_mask, protection_mask, req.protection_strength
    )

    # Compute risk scores per block and update them
    for block in req.blocks:
        block.risk_score = compute_risk_score(img, block, protection_mask)

    # Save masks
    cv2.imwrite(str(session_dir / "text_mask.png"), text_mask)
    cv2.imwrite(str(session_dir / "protection_mask.png"), protection_mask)
    cv2.imwrite(str(session_dir / "final_remove_mask.png"), final_mask)

    # Save updated text_layer with risk scores
    tl_path = session_dir / "text_layer.json"
    if tl_path.exists():
        import json
        tl = json.loads(tl_path.read_text(encoding="utf-8"))
        block_map = {b.id: b for b in req.blocks}
        for b in tl.get("blocks", []):
            if b["id"] in block_map:
                b["risk_score"] = block_map[b["id"]].risk_score
        tl_path.write_text(json.dumps(tl, indent=2, ensure_ascii=False), encoding="utf-8")

    base = f"/static/{req.session_id}"
    return MaskResponse(
        session_id=req.session_id,
        text_mask_url=f"{base}/text_mask.png",
        protection_mask_url=f"{base}/protection_mask.png",
        final_remove_mask_url=f"{base}/final_remove_mask.png",
    )
