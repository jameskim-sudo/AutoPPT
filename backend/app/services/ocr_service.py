"""
OCR 서비스 — PaddleOCR 기반 텍스트 검출 및 속성 추정

지원 언어: 한국어 + 영어 혼합
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional
import numpy as np
import cv2

from app.utils.color_utils import estimate_text_color, is_likely_bold
from app.utils.coordinate_transform import (
    calc_slide_dimensions,
    estimate_font_size_pt,
)
from app.utils.image_io import imread, imwrite

logger = logging.getLogger(__name__)

# PaddleOCR 인스턴스를 싱글톤으로 관리 (초기화 비용이 크다)
_ocr_instance: Optional[object] = None


def _ascii_base_dir() -> str:
    """
    항상 ASCII 문자만 포함된 기본 경로를 반환한다.

    Windows 한글 사용자명 경로 문제를 우회하기 위해
    드라이브 루트 바로 아래의 ASCII 경로를 사용한다.
      Windows → C:\paddleocr
      Linux/Mac → /tmp/paddleocr
    """
    import platform
    if platform.system() == "Windows":
        drive = os.environ.get("SYSTEMDRIVE", "C:")
        base = os.path.join(drive, os.sep, "paddleocr")
    else:
        base = "/tmp/paddleocr"
    os.makedirs(base, exist_ok=True)
    return base


def _safe_model_dir() -> str:
    return os.path.join(_ascii_base_dir(), "models")


def _safe_tmp_dir() -> str:
    """PaddleOCR에 넘길 임시 이미지를 저장할 ASCII 경로 디렉터리."""
    d = os.path.join(_ascii_base_dir(), "tmp")
    os.makedirs(d, exist_ok=True)
    return d


def _get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        import os
        from paddleocr import PaddleOCR  # type: ignore

        safe_dir = _safe_model_dir()
        logger.info("PaddleOCR 초기화 중... (모델 경로: %s)", safe_dir)

        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang="korean",        # 한국어 + 영어 혼합
            use_gpu=False,
            show_log=False,
            # 한글 경로 우회: ASCII 전용 경로에 모델 저장
            det_model_dir=os.path.join(safe_dir, "det"),
            rec_model_dir=os.path.join(safe_dir, "rec"),
            cls_model_dir=os.path.join(safe_dir, "cls"),
        )
        logger.info("PaddleOCR 초기화 완료")
    return _ocr_instance


def _box_to_xywh(box_points: list) -> tuple[float, float, float, float]:
    """
    [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] → (x_min, y_min, width, height)
    """
    xs = [p[0] for p in box_points]
    ys = [p[1] for p in box_points]
    x = float(min(xs))
    y = float(min(ys))
    w = float(max(xs) - x)
    h = float(max(ys) - y)
    return x, y, w, h


def _estimate_alignment(x: float, text_w: float, img_w: int) -> str:
    """텍스트 박스 중심 x 위치로 정렬 방향을 추정한다."""
    center_x = x + text_w / 2.0
    img_center = img_w / 2.0
    # 이미지 너비의 10% 이내이면 center
    if abs(center_x - img_center) < img_w * 0.10:
        return "center"
    # 오른쪽 끝에 붙어 있으면 right
    if (x + text_w) > img_w * 0.82:
        return "right"
    return "left"


def _split_into_lines(text: str, bbox_w: float, font_size_pt: float) -> List[str]:
    """
    텍스트를 박스 너비에 맞게 줄 분리한다.

    한글 한 글자 너비 ≈ font_size_pt × 0.9 픽셀 (72dpi 기준)
    영문 한 글자 너비 ≈ font_size_pt × 0.5 픽셀
    평균 ≈ font_size_pt × 0.7 를 사용
    """
    if not text:
        return []

    # 이미 줄바꿈이 포함된 경우
    if "\n" in text:
        return [l for l in text.split("\n") if l]

    char_w_px = max(1.0, font_size_pt * 0.7)
    chars_per_line = max(1, int(bbox_w / char_w_px))

    if len(text) <= chars_per_line:
        return [text]

    # 단어 단위 줄바꿈
    words = text.split()
    lines: List[str] = []
    cur = ""
    for word in words:
        candidate = f"{cur} {word}".strip() if cur else word
        if len(candidate) <= chars_per_line:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)

    return lines if lines else [text]


def _upscale_if_small(img: np.ndarray, min_side: int = 640) -> np.ndarray:
    """
    짧은 변이 min_side 미만이면 비율을 유지하며 업스케일한다.
    PaddleOCR은 너무 작은 이미지에서 정확도가 낮으므로 전처리로 보완한다.
    """
    h, w = img.shape[:2]
    short = min(h, w)
    if short >= min_side:
        return img
    scale = min_side / short
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)


def analyze_image(image_path: str) -> tuple[int, int, List[dict]]:
    """
    이미지를 분석하여 (image_width, image_height, blocks) 를 반환한다.

    작은 이미지도 자동 업스케일 후 OCR 처리 → 좌표는 원본 기준으로 역변환.

    blocks 각 항목:
      {
        id, text, bbox: {x,y,w,h}, fontSize, fontFamily,
        bold, italic, color, align, lineBreaks, confidence
      }
    """
    img = imread(image_path)
    orig_h, orig_w = img.shape[:2]

    # 작은 이미지 업스케일 (OCR 정확도 향상)
    img_scaled = _upscale_if_small(img, min_side=640)
    scaled_h, scaled_w = img_scaled.shape[:2]
    scale_x = orig_w / scaled_w  # 좌표 역변환 비율
    scale_y = orig_h / scaled_h

    # 업스케일된 이미지를 ASCII 전용 임시 경로에 저장 (PaddleOCR C++ 엔진 호환)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=_safe_tmp_dir()) as tmp:
        tmp_path = tmp.name
    imwrite(tmp_path, img_scaled)

    # OCR 실행
    try:
        ocr = _get_ocr()
        raw = ocr.ocr(tmp_path, cls=True)
    except Exception as exc:
        logger.error("OCR 실패: %s", exc)
        raise RuntimeError(f"OCR 처리 중 오류 발생: {exc}") from exc
    finally:
        os.unlink(tmp_path)

    if not raw or not raw[0]:
        logger.warning("OCR 결과 없음: %s", image_path)
        return orig_w, orig_h, []

    # 슬라이드 기준 좌표 (폰트 크기 추정에 사용) — 원본 크기 기준
    slide_w_emu, slide_h_emu = calc_slide_dimensions(orig_w, orig_h)

    blocks: List[dict] = []
    for idx, line in enumerate(raw[0]):
        if not line:
            continue
        box_points, (text, conf) = line

        # 스케일된 좌표 → 원본 좌표로 역변환
        x, y, w, h = _box_to_xywh(box_points)
        x *= scale_x
        y *= scale_y
        w *= scale_x
        h *= scale_y

        # 이미지 경계 안으로 클램핑
        x = max(0.0, min(x, orig_w - 1))
        y = max(0.0, min(y, orig_h - 1))
        w = min(w, orig_w - x)
        h = min(h, orig_h - y)

        if w <= 1 or h <= 1:
            continue

        text = text.strip()
        if not text:
            continue

        # 속성 추정 (원본 이미지 기준)
        line_count = max(1, text.count("\n") + 1)
        font_size = estimate_font_size_pt(h, orig_h, slide_h_emu, line_count)
        color = estimate_text_color(img, int(x), int(y), int(w), int(h))
        bold = is_likely_bold(h, font_size)
        align = _estimate_alignment(x, w, orig_w)
        line_breaks = _split_into_lines(text, w, font_size)

        blocks.append(
            {
                "id": f"block-{idx + 1}",
                "text": text,
                "bbox": {"x": x, "y": y, "w": w, "h": h},
                "fontSize": font_size,
                "fontFamily": "Malgun Gothic",
                "bold": bold,
                "italic": False,
                "color": color,
                "align": align,
                "lineBreaks": line_breaks,
                "confidence": round(float(conf), 4),
            }
        )

    logger.info("OCR 완료: %d 블록 검출 (원본 %dx%d)", len(blocks), orig_w, orig_h)
    return orig_w, orig_h, blocks
