"""
텍스트 제거(inpainting) 서비스

단계:
  1. bounding box 기반 마스크 생성
  2. 마스크 dilation (글자 외곽까지 커버)
  3. OpenCV inpaint (TELEA 또는 Navier-Stokes)
"""

import logging
from pathlib import Path
from typing import List
import numpy as np
import cv2

from app.utils.image_io import imread, imwrite

logger = logging.getLogger(__name__)


def _create_mask(
    shape: tuple[int, int],
    blocks: List[dict],
    dilation_kernel: int,
) -> np.ndarray:
    """
    텍스트 bounding box들을 흰색으로 채운 마스크를 생성한다.

    Args:
        shape:            (height, width)
        blocks:           TextBlock dict 리스트
        dilation_kernel:  마스크 팽창 커널 크기 (홀수 권장)

    Returns:
        uint8 마스크 (255=인페인트 대상, 0=배경)
    """
    h, w = shape
    mask = np.zeros((h, w), dtype=np.uint8)

    for block in blocks:
        bbox = block.get("bbox", {})
        bx = max(0, int(bbox.get("x", 0)))
        by = max(0, int(bbox.get("y", 0)))
        bw = int(bbox.get("w", 0))
        bh = int(bbox.get("h", 0))

        # 경계 클램핑
        x2 = min(w, bx + bw)
        y2 = min(h, by + bh)
        if x2 <= bx or y2 <= by:
            continue

        mask[by:y2, bx:x2] = 255

    # 마스크 팽창으로 글자 경계부 제거
    if dilation_kernel > 1:
        k = dilation_kernel if dilation_kernel % 2 == 1 else dilation_kernel + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
        mask = cv2.dilate(mask, kernel, iterations=1)

    return mask


def remove_text(
    image_path: str,
    blocks: List[dict],
    dilation_kernel: int = 5,
    inpaint_radius: int = 3,
    inpaint_method: str = "telea",
) -> np.ndarray:
    """
    이미지에서 텍스트를 인페인팅으로 제거한다.

    Args:
        image_path:       입력 이미지 경로
        blocks:           제거할 TextBlock dict 리스트
        dilation_kernel:  마스크 팽창 크기 (1~30)
        inpaint_radius:   인페인트 반경 (픽셀)
        inpaint_method:   "telea" | "ns"

    Returns:
        텍스트가 제거된 BGR numpy array
    """
    img = imread(image_path)

    h, w = img.shape[:2]
    logger.info("인페인트 시작: %dx%d, 블록=%d", w, h, len(blocks))

    mask = _create_mask((h, w), blocks, dilation_kernel)

    method_flag = cv2.INPAINT_TELEA if inpaint_method == "telea" else cv2.INPAINT_NS

    try:
        result = cv2.inpaint(img, mask, inpaint_radius, method_flag)
    except Exception as exc:
        logger.error("인페인트 실패: %s", exc)
        raise RuntimeError(f"텍스트 제거 처리 중 오류: {exc}") from exc

    logger.info("인페인트 완료")
    return result


def save_cleaned_image(cleaned: np.ndarray, output_path: str) -> None:
    """인페인트 결과를 PNG로 저장한다 (한글 경로 호환)."""
    imwrite(output_path, cleaned, ext=".png")
