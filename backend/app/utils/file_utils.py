"""
파일 관련 유틸리티
"""

import uuid
import shutil
from pathlib import Path
from fastapi import HTTPException, UploadFile

from app.config import UPLOAD_DIR, RESULTS_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB


def new_id() -> str:
    return uuid.uuid4().hex


def get_upload_path(image_id: str, suffix: str = ".png") -> Path:
    return UPLOAD_DIR / f"{image_id}{suffix}"


def get_result_path(file_id: str, suffix: str = ".pptx") -> Path:
    return RESULTS_DIR / f"{file_id}{suffix}"


def get_cleaned_path(image_id: str) -> Path:
    return UPLOAD_DIR / f"{image_id}_cleaned.png"


async def save_upload(upload: UploadFile) -> tuple[str, Path]:
    """
    업로드된 파일을 저장하고 (image_id, path) 를 반환한다.
    """
    # 확장자 검사
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 파일 크기 검사
    contents = await upload.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"파일 크기가 {MAX_FILE_SIZE_MB}MB를 초과합니다.",
        )

    image_id = new_id()
    dest = get_upload_path(image_id, suffix)
    dest.write_bytes(contents)
    return image_id, dest


def require_file(path: Path, label: str = "파일") -> Path:
    """파일이 존재하지 않으면 404를 발생시킨다."""
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{label}을 찾을 수 없습니다: {path.name}")
    return path
