"""
POST /api/generate-ppt

PPTX 파일을 생성하고 다운로드 URL을 반환한다.
"""

import logging
from fastapi import APIRouter, HTTPException

from app.models.schemas import GeneratePPTRequest, GeneratePPTResponse
from app.services import ppt_service
from app.utils.file_utils import new_id, get_result_path, get_cleaned_path
from app.config import UPLOAD_DIR, RESULTS_DIR

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate-ppt", response_model=GeneratePPTResponse)
async def generate_ppt(req: GeneratePPTRequest):
    """
    텍스트 제거된 배경 이미지와 편집된 텍스트 블록으로 PPTX를 생성한다.

    - 슬라이드 크기 = 원본 이미지 비율과 동일
    - 배경 = 클린 이미지 전체 채움
    - 각 블록 = editable 텍스트 박스 (fill/border 없음)
    """
    # 클린 이미지 파일 확인
    cleaned_path = get_cleaned_path(req.image_id)
    if not cleaned_path.exists():
        raise HTTPException(
            status_code=404,
            detail="텍스트 제거된 이미지를 찾을 수 없습니다. /api/inpaint-text 를 먼저 실행하세요.",
        )

    blocks_dict = [b.model_dump() for b in req.blocks]

    # 출력 파일 경로
    file_id = new_id()
    output_path = get_result_path(file_id, ".pptx")

    try:
        ppt_service.generate_pptx(
            cleaned_image_path=str(cleaned_path),
            blocks=blocks_dict,
            image_width=req.image_width,
            image_height=req.image_height,
            output_path=str(output_path),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("PPT 생성 오류: %s", exc)
        raise HTTPException(status_code=500, detail=f"PPTX 생성 중 오류: {exc}")

    download_url = f"/api/download/{file_id}"
    logger.info("PPTX 생성 완료: %s", file_id)

    return GeneratePPTResponse(file_id=file_id, download_url=download_url)
