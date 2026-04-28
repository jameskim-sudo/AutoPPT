from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import upload, detect, masks, remove, restore, download

WORKSPACE = Path("workspace")
WORKSPACE.mkdir(exist_ok=True)

app = FastAPI(
    title="Text Layer Separator",
    description="Upload an image → separate text layer → restore background",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(WORKSPACE)), name="static")

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(detect.router, prefix="/api", tags=["detect"])
app.include_router(masks.router, prefix="/api", tags=["masks"])
app.include_router(remove.router, prefix="/api", tags=["remove"])
app.include_router(restore.router, prefix="/api", tags=["restore"])
app.include_router(download.router, prefix="/api", tags=["download"])


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
