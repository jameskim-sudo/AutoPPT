"""
이미지 영역에서 텍스트 색상을 추정하는 유틸리티
"""

import numpy as np
import cv2
from typing import Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """#rrggbb → (r, g, b)"""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (0, 0, 0)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """(r, g, b) → #rrggbb"""
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b)),
    )


def estimate_text_color(
    img_bgr: np.ndarray,
    x: int,
    y: int,
    w: int,
    h: int,
    dark_percentile: float = 15.0,
) -> str:
    """
    bounding box 내 가장 어두운 픽셀들의 평균 색상을 텍스트 색상으로 추정한다.

    밝은 배경에 어두운 텍스트를 가정. 만약 배경이 어두운 경우
    (배경 평균 밝기 < 128) 밝은 픽셀을 대신 샘플링한다.

    Args:
        img_bgr:        BGR 이미지 (numpy ndarray)
        x, y, w, h:     bounding box (픽셀)
        dark_percentile: 하위 몇 % 픽셀을 텍스트로 볼 것인지

    Returns:
        "#rrggbb" 형식의 추정 색상 문자열
    """
    try:
        ih, iw = img_bgr.shape[:2]
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1 = min(iw, int(x + w))
        y1 = min(ih, int(y + h))

        roi = img_bgr[y0:y1, x0:x1]
        if roi.size == 0:
            return "#000000"

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        mean_gray = float(np.mean(gray))

        # 어두운 배경이면 밝은 픽셀을 텍스트 색으로
        if mean_gray < 128:
            threshold = np.percentile(gray, 100 - dark_percentile)
            mask = gray >= threshold
        else:
            threshold = np.percentile(gray, dark_percentile)
            mask = gray <= threshold

        if not np.any(mask):
            return "#000000"

        roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
        sampled = roi_rgb[mask]
        avg = sampled.mean(axis=0).astype(int)
        return rgb_to_hex(int(avg[0]), int(avg[1]), int(avg[2]))

    except Exception:
        return "#000000"


def is_likely_bold(bbox_h: float, font_size_pt: float) -> bool:
    """
    bounding box 높이와 추정 폰트 크기를 비교해 Bold 여부를 추정한다.
    Bold 폰트는 같은 포인트 크기에서 획이 두껍기 때문에 bbox 비율이 크다.
    """
    if font_size_pt <= 0:
        return False
    ratio = bbox_h / font_size_pt
    # 일반적으로 폰트 pt ≈ px (96dpi 기준) 이므로 ratio > 1.15 이면 Bold 가능성 높음
    return ratio > 1.15
