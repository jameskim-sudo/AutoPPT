"""
POST /api/upload-image

이미지를 서버에 업로드한다.
반환: image_id, 파일 정보, 이미지 URL
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image

from app.models.schemas import UploadResponse
from app.utils.file_utils import save_upload

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload-image", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """이미지 파일을 업로드하고 image_id를 반환한다."""
    try:
        image_id, dest = await save_upload(file)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("업로드 실패: %s", exc)
        raise HTTPException(status_code=500, detail=f"업로드 처리 중 오류: {exc}")

    # 이미지 크기 확인
    try:
        with Image.open(dest) as img:
            width, height = img.size
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"이미지 파일 파싱 실패: {exc}")

    image_url = f"/uploads/{dest.name}"
    logger.info("업로드 완료: %s (%dx%d)", image_id, width, height)

    return UploadResponse(
        image_id=image_id,
        filename=file.filename or dest.name,
        width=width,
        height=height,
        image_url=image_url,
    )
