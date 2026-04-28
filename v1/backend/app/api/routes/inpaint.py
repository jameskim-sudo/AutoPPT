"""
POST /api/inpaint-text

텍스트 제거(inpainting)를 수행하고 클린 이미지를 저장한다.
"""

import logging
from fastapi import APIRouter, HTTPException

from app.models.schemas import InpaintRequest, InpaintResponse
from app.services import inpaint_service
from app.utils.file_utils import new_id, get_cleaned_path
from app.config import UPLOAD_DIR

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/inpaint-text", response_model=InpaintResponse)
async def inpaint_text(req: InpaintRequest):
    """
    텍스트 bounding box를 마스크로 사용해 인페인팅을 수행한다.

    - dilation_kernel: 마스크 팽창 크기 (기본 5)
    - inpaint_radius:  인페인트 반경 (기본 3)
    - inpaint_method:  "telea" | "ns" (기본 telea)
    """
    # 원본 이미지 파일 찾기
    candidates = list(UPLOAD_DIR.glob(f"{req.image_id}.*"))
    candidates = [p for p in candidates if "_cleaned" not in p.name]
    if not candidates:
        raise HTTPException(status_code=404, detail=f"image_id '{req.image_id}' 를 찾을 수 없습니다.")
    image_path = str(candidates[0])

    blocks_dict = [b.model_dump() for b in req.blocks]

    try:
        cleaned = inpaint_service.remove_text(
            image_path=image_path,
            blocks=blocks_dict,
            dilation_kernel=req.dilation_kernel,
            inpaint_radius=req.inpaint_radius,
            inpaint_method=req.inpaint_method,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.error("인페인트 오류: %s", exc)
        raise HTTPException(status_code=500, detail=f"텍스트 제거 처리 중 오류: {exc}")

    # 클린 이미지 저장
    cleaned_image_id = f"{req.image_id}_cleaned"
    cleaned_path = get_cleaned_path(req.image_id)
    try:
        inpaint_service.save_cleaned_image(cleaned, str(cleaned_path))
    except IOError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    cleaned_image_url = f"/uploads/{cleaned_path.name}"
    logger.info("인페인트 완료: %s", cleaned_path.name)

    return InpaintResponse(
        cleaned_image_id=cleaned_image_id,
        cleaned_image_url=cleaned_image_url,
    )
