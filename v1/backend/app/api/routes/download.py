"""
GET /api/download/{file_id}

생성된 PPTX 파일을 다운로드한다.
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.utils.file_utils import get_result_path

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/download/{file_id}")
async def download_pptx(file_id: str):
    """생성된 PPTX 파일을 다운로드한다."""
    # 경로 트래버설 방지: file_id 에 / 또는 .. 포함 불가
    if "/" in file_id or ".." in file_id:
        raise HTTPException(status_code=400, detail="잘못된 file_id 입니다.")

    path = get_result_path(file_id, ".pptx")
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {file_id}")

    logger.info("다운로드: %s", path.name)
    return FileResponse(
        path=str(path),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename="autoppt_result.pptx",
    )
