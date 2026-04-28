import io
import zipfile
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

router = APIRouter()
WORKSPACE = Path("workspace")

DOWNLOADABLE = {
    "result": "restored_background.png",
    "clean": "clean_background.png",
    "text-layer": "text_layer.json",
    "text-mask": "text_mask.png",
    "protection-mask": "protection_mask.png",
    "final-mask": "final_remove_mask.png",
    "original": "original.png",
}


@router.get("/download/{session_id}/{file_key}")
async def download_file(session_id: str, file_key: str):
    filename = DOWNLOADABLE.get(file_key)
    if filename is None:
        raise HTTPException(400, f"Unknown file key: {file_key}")

    path = WORKSPACE / session_id / filename
    if not path.exists():
        raise HTTPException(404, f"{filename} has not been generated yet.")

    return FileResponse(
        path=str(path),
        filename=filename,
        media_type="application/octet-stream",
    )


@router.get("/download/{session_id}/debug/zip")
async def download_debug_zip(session_id: str):
    session_dir = WORKSPACE / session_id
    if not session_dir.exists():
        raise HTTPException(404, "Session not found.")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath in session_dir.iterdir():
            if fpath.is_file():
                zf.write(fpath, arcname=fpath.name)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=debug_{session_id[:8]}.zip"},
    )
