"""
OCR 서비스 — PaddleOCR 기반 텍스트 검출 및 속성 추정

지원 언어: 한국어 + 영어 혼합
"""

import logging
from pathlib import Path
from typing import List, Optional
import numpy as np
import cv2

from app.utils.color_utils import estimate_text_color, is_likely_bold
from app.utils.coordinate_transform import (
    calc_slide_dimensions,
    estimate_font_size_pt,
)

logger = logging.getLogger(__name__)

# PaddleOCR 인스턴스를 싱글톤으로 관리 (초기화 비용이 크다)
_ocr_instance: Optional[object] = None


def _get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        from paddleocr import PaddleOCR  # type: ignore

        logger.info("PaddleOCR 초기화 중...")
        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang="korean",        # 한국어 + 영어 혼합
            use_gpu=False,
            show_log=False,
            ocr_version="PP-OCRv4",
            rec_batch_num=6,
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


def analyze_image(image_path: str) -> tuple[int, int, List[dict]]:
    """
    이미지를 분석하여 (image_width, image_height, blocks) 를 반환한다.

    blocks 각 항목:
      {
        id, text, bbox: {x,y,w,h}, fontSize, fontFamily,
        bold, italic, color, align, lineBreaks, confidence
      }
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")

    img_h, img_w = img.shape[:2]

    # OCR 실행
    try:
        ocr = _get_ocr()
        raw = ocr.ocr(image_path, cls=True)
    except Exception as exc:
        logger.error("OCR 실패: %s", exc)
        raise RuntimeError(f"OCR 처리 중 오류 발생: {exc}") from exc

    if not raw or not raw[0]:
        logger.warning("OCR 결과 없음: %s", image_path)
        return img_w, img_h, []

    # 슬라이드 기준 좌표 (폰트 크기 추정에 사용)
    slide_w_emu, slide_h_emu = calc_slide_dimensions(img_w, img_h)

    blocks: List[dict] = []
    for idx, line in enumerate(raw[0]):
        if not line:
            continue
        box_points, (text, conf) = line

        # 좌표 변환
        x, y, w, h = _box_to_xywh(box_points)

        # 이미지 경계 안으로 클램핑
        x = max(0.0, min(x, img_w - 1))
        y = max(0.0, min(y, img_h - 1))
        w = min(w, img_w - x)
        h = min(h, img_h - y)

        if w <= 2 or h <= 2:
            continue

        text = text.strip()
        if not text:
            continue

        # 속성 추정
        line_count = max(1, text.count("\n") + 1)
        font_size = estimate_font_size_pt(h, img_h, slide_h_emu, line_count)
        color = estimate_text_color(img, int(x), int(y), int(w), int(h))
        bold = is_likely_bold(h, font_size)
        align = _estimate_alignment(x, w, img_w)
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

    logger.info("OCR 완료: %d 블록 검출", len(blocks))
    return img_w, img_h, blocks
