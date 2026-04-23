"""
AutoPPT — FastAPI 백엔드 진입점
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import CORS_ORIGINS, UPLOAD_DIR, RESULTS_DIR
from app.api.routes import upload, analyze, inpaint, generate_ppt, download

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AutoPPT 서버 시작")
    logger.info("업로드 디렉터리: %s", UPLOAD_DIR.resolve())
    logger.info("결과 디렉터리:   %s", RESULTS_DIR.resolve())
    yield
    logger.info("AutoPPT 서버 종료")


app = FastAPI(
    title="AutoPPT API",
    version="1.0.0",
    description="이미지 → editable PPTX 변환 서비스",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 정적 파일 서빙 ───────────────────────────────────────────────────────────
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/results", StaticFiles(directory=str(RESULTS_DIR)), name="results")

# ── 라우터 등록 ──────────────────────────────────────────────────────────────
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(inpaint.router, prefix="/api", tags=["inpaint"])
app.include_router(generate_ppt.router, prefix="/api", tags=["ppt"])
app.include_router(download.router, prefix="/api", tags=["download"])


# ── 전역 예외 핸들러 ─────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("처리되지 않은 예외: %s %s — %s", request.method, request.url, exc)
    return JSONResponse(
        status_code=500,
        content={"error": "서버 내부 오류", "detail": str(exc)},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "AutoPPT"}
