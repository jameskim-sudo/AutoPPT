import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple

from models.schemas import TextBlock


def create_text_mask(image_path: Path, blocks: List[TextBlock], img_size: Tuple[int, int]) -> np.ndarray:
    """
    Create a precise text mask.
    For each block:
      1. Fill polygon to get initial region
      2. Within that region, use adaptive threshold + connected component analysis
         to isolate actual stroke pixels (not entire bbox rectangle)
      3. If refined result is too sparse, fall back to polygon fill
      4. Apply minimal dilation
    """
    H, W = img_size
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    text_mask = np.zeros((H, W), dtype=np.uint8)

    for block in blocks:
        polygon = np.array(block.polygon, dtype=np.int32)
        poly_mask = np.zeros((H, W), dtype=np.uint8)
        cv2.fillPoly(poly_mask, [polygon], 255)

        x, y = block.bbox.x, block.bbox.y
        bw, bh = block.bbox.w, block.bbox.h

        pad = 4
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(W, x + bw + pad)
        y2 = min(H, y + bh + pad)
        roi_h = y2 - y1
        roi_w = x2 - x1

        if roi_h < 2 or roi_w < 2:
            text_mask = cv2.bitwise_or(text_mask, poly_mask)
            continue

        roi = gray[y1:y2, x1:x2]

        # Adaptive threshold: dark text on light background
        block_size = max(3, (min(roi_h, roi_w) // 4) * 2 + 1)
        block_size = min(block_size, 31)
        thresh_dark = cv2.adaptiveThreshold(
            roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, block_size, 3
        )

        # Otsu: handles light text on dark background
        _, thresh_light = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        _, thresh_light2 = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Keep letter-sized components from each threshold
        refined_dark = _keep_text_components(thresh_dark, roi_h, roi_w)
        refined_light = _keep_text_components(thresh_light, roi_h, roi_w)
        refined_light2 = _keep_text_components(thresh_light2, roi_h, roi_w)

        combined = cv2.bitwise_or(refined_dark, refined_light)
        combined = cv2.bitwise_or(combined, refined_light2)

        # Place refined mask back into full mask
        full_refined = np.zeros((H, W), dtype=np.uint8)
        full_refined[y1:y2, x1:x2] = combined

        # Only keep pixels inside polygon
        full_refined = cv2.bitwise_and(full_refined, poly_mask)

        # Fall back to polygon if refined coverage is too low
        poly_area = float(np.sum(poly_mask > 0))
        refined_area = float(np.sum(full_refined > 0))
        if poly_area > 0 and refined_area / poly_area < 0.08:
            text_mask = cv2.bitwise_or(text_mask, poly_mask)
        else:
            text_mask = cv2.bitwise_or(text_mask, full_refined)

    # Minimal dilation to close small gaps in strokes
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    text_mask = cv2.dilate(text_mask, kernel, iterations=1)

    return text_mask


def _keep_text_components(binary: np.ndarray, roi_h: int, roi_w: int) -> np.ndarray:
    """Keep connected components that are letter-sized (not noise, not large structures)."""
    min_area = 4
    max_area = roi_h * roi_w * 0.25
    max_single_dim = min(roi_h, roi_w) * 0.9

    num, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    result = np.zeros_like(binary)

    for lbl in range(1, num):
        area = stats[lbl, cv2.CC_STAT_AREA]
        cw = stats[lbl, cv2.CC_STAT_WIDTH]
        ch = stats[lbl, cv2.CC_STAT_HEIGHT]

        if area < min_area:
            continue
        if area > max_area:
            continue
        if cw > max_single_dim and ch > max_single_dim:
            continue

        result[labels == lbl] = 255

    return result


def create_protection_mask(image_path: Path, img_size: Tuple[int, int]) -> np.ndarray:
    """
    Create a protection mask that covers non-text structural elements:
    lines, borders, icons, graphs, arrows, table lines, photos.
    """
    H, W = img_size
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    protection = np.zeros((H, W), dtype=np.uint8)

    # --- 1. Detect straight lines via HoughLinesP ---
    edges = cv2.Canny(gray, 40, 120, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges, rho=1, theta=np.pi / 180,
        threshold=40, minLineLength=25, maxLineGap=8
    )
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(protection, (x1, y1), (x2, y2), 255, thickness=8)

    # --- 2. Large structural contours (icons, card borders, graphs) ---
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
        area = cv2.contourArea(c)
        if area < 300:
            continue
        if area > H * W * 0.6:
            continue

        x, y, cw, ch = cv2.boundingRect(c)
        aspect = cw / max(ch, 1)

        # Skip very wide, thin text-like runs
        if aspect > 8 and ch < 20:
            continue

        # Protect medium-to-large structures with thick contour
        cv2.drawContours(protection, [c], -1, 255, thickness=4)

    # --- 3. Edge dilation around detected lines ---
    edge_near_lines = np.zeros_like(protection)
    if lines is not None:
        line_mask = np.zeros((H, W), dtype=np.uint8)
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(line_mask, (x1, y1), (x2, y2), 255, thickness=14)
        edge_dilated = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
        edge_near_lines = cv2.bitwise_and(edge_dilated, line_mask)

    protection = cv2.bitwise_or(protection, edge_near_lines)

    # Smooth out the protection mask slightly
    protection = cv2.dilate(protection, np.ones((3, 3), np.uint8), iterations=1)

    return protection


def create_final_remove_mask(
    text_mask: np.ndarray,
    protection_mask: np.ndarray,
    protection_strength: float = 1.0,
) -> np.ndarray:
    """
    final_remove_mask = text_mask - protection_mask
    protection_strength in [0, 1]: 0 = ignore protection, 1 = full protection
    """
    if protection_strength <= 0:
        return text_mask.copy()

    if protection_strength < 1.0:
        # Erode protection to weaken it
        erode_px = max(1, int(7 * (1.0 - protection_strength)))
        kernel = np.ones((erode_px * 2 + 1, erode_px * 2 + 1), np.uint8)
        scaled_protection = cv2.erode(protection_mask, kernel, iterations=1)
    else:
        scaled_protection = protection_mask

    final = cv2.bitwise_and(text_mask, cv2.bitwise_not(scaled_protection))
    return final


def compute_risk_score(
    img: np.ndarray,
    block: TextBlock,
    protection_mask: np.ndarray,
) -> float:
    """
    Risk score [0, 1]:
      - High overlap with protection_mask → high risk
      - Low OCR confidence → higher risk
      - Very small text area relative to block bbox → higher risk
    """
    x, y = block.bbox.x, block.bbox.y
    w, h = block.bbox.w, block.bbox.h
    H, W = img.shape[:2]

    x2 = min(W, x + w)
    y2 = min(H, y + h)

    region_prot = protection_mask[y:y2, x:x2]
    bbox_area = max((x2 - x) * (y2 - y), 1)
    prot_ratio = float(np.sum(region_prot > 0)) / bbox_area

    conf_penalty = 1.0 - float(block.confidence)

    # Check if block is near image edges (higher risk)
    edge_margin = 0.05
    near_edge = (
        x < W * edge_margin or y < H * edge_margin
        or (x + w) > W * (1 - edge_margin)
        or (y + h) > H * (1 - edge_margin)
    )
    edge_penalty = 0.15 if near_edge else 0.0

    risk = 0.55 * prot_ratio + 0.30 * conf_penalty + edge_penalty
    return round(min(1.0, max(0.0, risk)), 3)
