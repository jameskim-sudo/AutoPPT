import cv2
import numpy as np
from pathlib import Path
from typing import List

from models.schemas import TextBlock, BBox

# PaddleOCR is loaded lazily on first use
_ocr_instance = None
PADDLE_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    pass


def _get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang="korean",
            show_log=False,
            use_gpu=False,
        )
    return _ocr_instance


def _polygon_to_bbox(polygon: List[List[int]]) -> BBox:
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return BBox(x=min(xs), y=min(ys), w=max(xs) - min(xs), h=max(ys) - min(ys))


def detect_text(image_path: Path) -> List[TextBlock]:
    if PADDLE_AVAILABLE:
        try:
            return _detect_with_paddle(image_path)
        except Exception as e:
            print(f"[WARN] PaddleOCR failed ({e}), falling back to MSER")
    return _detect_fallback(image_path)


def _detect_with_paddle(image_path: Path) -> List[TextBlock]:
    ocr = _get_ocr()
    result = ocr.ocr(str(image_path), cls=True)

    blocks: List[TextBlock] = []
    if not result or not result[0]:
        return blocks

    for i, line in enumerate(result[0]):
        if line is None:
            continue
        polygon_raw, (text, confidence) = line
        polygon = [[int(round(p[0])), int(round(p[1]))] for p in polygon_raw]
        bbox = _polygon_to_bbox(polygon)

        # Skip degenerate boxes
        if bbox.w < 4 or bbox.h < 4:
            continue

        blocks.append(TextBlock(
            id=f"text-{i:03d}",
            text=text,
            bbox=bbox,
            polygon=polygon,
            confidence=float(confidence),
        ))

    return blocks


def _detect_fallback(image_path: Path) -> List[TextBlock]:
    """Simple EAST-style fallback using MSER when PaddleOCR is not available."""
    img = cv2.imread(str(image_path))
    if img is None:
        return []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    H, W = gray.shape

    mser = cv2.MSER_create(min_area=60, max_area=int(H * W * 0.02))
    regions, bboxes = mser.detectRegions(gray)

    # Merge overlapping bboxes
    merged = _merge_bboxes(bboxes.tolist(), W, H)

    blocks: List[TextBlock] = []
    for i, (x, y, w, h) in enumerate(merged[:80]):
        polygon = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
        blocks.append(TextBlock(
            id=f"text-{i:03d}",
            text="(OCR unavailable)",
            bbox=BBox(x=x, y=y, w=w, h=h),
            polygon=polygon,
            confidence=0.5,
        ))

    return blocks


def _merge_bboxes(bboxes: list, W: int, H: int, overlap_thresh: float = 0.3) -> list:
    """Merge overlapping bounding boxes."""
    if not bboxes:
        return []

    # Filter: reasonable text proportions
    filtered = []
    for x, y, w, h in bboxes:
        if w < 8 or h < 6:
            continue
        if w > W * 0.7:
            continue
        aspect = w / max(h, 1)
        if aspect > 20 or aspect < 0.1:
            continue
        filtered.append([int(x), int(y), int(w), int(h)])

    if not filtered:
        return []

    # Convert to [x1, y1, x2, y2] format
    boxes = [[b[0], b[1], b[0] + b[2], b[1] + b[3]] for b in filtered]
    boxes.sort(key=lambda b: (b[1], b[0]))

    merged = []
    used = [False] * len(boxes)

    for i in range(len(boxes)):
        if used[i]:
            continue
        x1, y1, x2, y2 = boxes[i]
        for j in range(i + 1, len(boxes)):
            if used[j]:
                continue
            bx1, by1, bx2, by2 = boxes[j]
            # Intersection
            ix1, iy1 = max(x1, bx1), max(y1, by1)
            ix2, iy2 = min(x2, bx2), min(y2, by2)
            if ix2 > ix1 and iy2 > iy1:
                inter = (ix2 - ix1) * (iy2 - iy1)
                area_a = (x2 - x1) * (y2 - y1)
                area_b = (bx2 - bx1) * (by2 - by1)
                iou = inter / min(area_a, area_b)
                if iou > overlap_thresh:
                    x1 = min(x1, bx1)
                    y1 = min(y1, by1)
                    x2 = max(x2, bx2)
                    y2 = max(y2, by2)
                    used[j] = True
        used[i] = True
        merged.append((x1, y1, x2 - x1, y2 - y1))

    return merged
