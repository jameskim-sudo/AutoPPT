import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from PIL import Image

from models.schemas import UploadResponse
from utils.image_utils import normalize_to_png

router = APIRouter()
WORKSPACE = Path("workspace")


@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in ("image/png", "image/jpeg", "image/jpg"):
        raise HTTPException(400, "Unsupported file type. Use PNG or JPEG.")

    session_id = uuid.uuid4().hex
    session_dir = WORKSPACE / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Save original bytes
    ext = Path(file.filename).suffix.lower()
    raw_path = session_dir / f"upload{ext}"
    content = await file.read()
    raw_path.write_bytes(content)

    # Normalize to PNG
    original_path = session_dir / "original.png"
    normalize_to_png(raw_path, original_path)
    raw_path.unlink(missing_ok=True)

    with Image.open(original_path) as im:
        width, height = im.size

    return UploadResponse(
        session_id=session_id,
        original_url=f"/static/{session_id}/original.png",
        width=width,
        height=height,
        filename=file.filename,
    )
