"""
POST /api/analyze-image

업로드된 이미지에서 텍스트를 검출하고 bounding box + 속성을 반환한다.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schemas import AnalyzeResponse
from app.services import ocr_service
from app.config import UPLOAD_DIR

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalyzeRequest(BaseModel):
    image_id: str


@router.post("/analyze-image", response_model=AnalyzeResponse)
async def analyze_image(req: AnalyzeRequest):
    """
    OCR로 텍스트 블록을 검출한다.

    - PaddleOCR PP-OCRv4 (korean 모델)
    - 반환: 블록별 text, bbox, fontSize, color, bold, align, lineBreaks
    """
    # 업로드 파일 찾기 (확장자 무관)
    candidates = list(UPLOAD_DIR.glob(f"{req.image_id}.*"))
    candidates = [p for p in candidates if "_cleaned" not in p.name]
    if not candidates:
        raise HTTPException(status_code=404, detail=f"image_id '{req.image_id}' 를 찾을 수 없습니다.")
    image_path = str(candidates[0])

    try:
        img_w, img_h, blocks = ocr_service.analyze_image(image_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("분석 오류: %s", exc)
        raise HTTPException(status_code=500, detail=f"이미지 분석 중 오류: {exc}")

    return AnalyzeResponse(
        image_id=req.image_id,
        image_width=img_w,
        image_height=img_h,
        blocks=blocks,  # type: ignore[arg-type]
    )
