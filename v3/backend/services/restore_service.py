"""
Background restoration service.

Processing pipeline per block:
  crop patch (with padding)
  → classify background type
  → select restoration mode
  → restore patch
  → quality check  (rollback if below threshold)
  → color match
  → feather blend
  → write back to result image
"""

import cv2
import numpy as np
import json
from pathlib import Path
from typing import List, Tuple

from models.schemas import TextBlock, ProcessingMode, RestoreStatus

QUALITY_THRESHOLD = 0.38


# ---------------------------------------------------------------------------
# Background classification
# ---------------------------------------------------------------------------

def classify_background(patch: np.ndarray, mask: np.ndarray) -> str:
    """
    Returns one of: 'solid', 'gradient', 'panel', 'photo'
    Samples pixels outside the mask to characterize the background.
    """
    mask_bool = mask > 0
    outside = ~mask_bool
    if outside.sum() < 10:
        return "photo"

    pixels = patch[outside].reshape(-1, 3).astype(np.float32)

    std = float(np.std(pixels, axis=0).mean())

    if std < 10:
        return "solid"

    if std < 28:
        h, w = patch.shape[:2]
        # Check gradient direction: compare top quarter vs bottom quarter
        top_mask = np.zeros_like(mask_bool)
        top_mask[:h // 4, :] = True
        bot_mask = np.zeros_like(mask_bool)
        bot_mask[3 * h // 4:, :] = True

        top_px = patch[top_mask & outside]
        bot_px = patch[bot_mask & outside]

        if len(top_px) > 4 and len(bot_px) > 4:
            diff = float(np.abs(
                np.mean(top_px.reshape(-1, 3), axis=0) - np.mean(bot_px.reshape(-1, 3), axis=0)
            ).mean())
            if diff > 12:
                return "gradient"

        return "panel"

    return "photo"


# ---------------------------------------------------------------------------
# Restoration modes
# ---------------------------------------------------------------------------

def _restore_safe_fill(patch: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Fill masked area with median color of surrounding ring."""
    result = patch.copy()
    mask_bool = mask > 0

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))
    dilated = cv2.dilate(mask, kernel)
    ring = (dilated > 0) & ~mask_bool

    if ring.sum() < 4:
        src = patch[~mask_bool]
        fill = np.median(src.reshape(-1, 3), axis=0) if len(src) else np.array([128, 128, 128])
    else:
        fill = np.median(patch[ring].reshape(-1, 3), axis=0)

    result[mask_bool] = fill.astype(np.uint8)
    return result


def _restore_gradient(patch: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Bilinear interpolation: for each masked pixel, find nearest unmasked
    pixel in each of the 4 cardinal directions, then weight-average.
    """
    result = patch.copy().astype(np.float32)
    h, w = patch.shape[:2]
    mask_bool = mask > 0

    ys, xs = np.where(mask_bool)

    for y, x in zip(ys, xs):
        neighbors = []

        # Left
        for dx in range(x - 1, -1, -1):
            if not mask_bool[y, dx]:
                neighbors.append((patch[y, dx].astype(float), x - dx))
                break
        # Right
        for dx in range(x + 1, w):
            if not mask_bool[y, dx]:
                neighbors.append((patch[y, dx].astype(float), dx - x))
                break
        # Up
        for dy in range(y - 1, -1, -1):
            if not mask_bool[dy, x]:
                neighbors.append((patch[dy, x].astype(float), y - dy))
                break
        # Down
        for dy in range(y + 1, h):
            if not mask_bool[dy, x]:
                neighbors.append((patch[dy, x].astype(float), dy - y))
                break

        if neighbors:
            colors = np.array([n[0] for n in neighbors])
            dists = np.array([n[1] for n in neighbors], dtype=np.float32)
            weights = 1.0 / (dists + 1e-6)
            weights /= weights.sum()
            result[y, x] = np.dot(weights, colors)

    return result.astype(np.uint8)


def _restore_panel(patch: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Fill with dominant background color in non-masked area."""
    result = patch.copy()
    mask_bool = mask > 0
    non_mask = patch[~mask_bool].reshape(-1, 3)

    if len(non_mask) == 0:
        return result

    # Use 25th–75th percentile to avoid outliers
    fill = np.percentile(non_mask, 50, axis=0).astype(np.uint8)
    result[mask_bool] = fill
    return result


def _restore_inpaint(patch: np.ndarray, mask: np.ndarray, radius: int = 4) -> np.ndarray:
    return cv2.inpaint(patch, mask, inpaintRadius=radius, flags=cv2.INPAINT_TELEA)


def restore_with_mode(patch: np.ndarray, mask: np.ndarray, mode: str) -> np.ndarray:
    if mode in ("keep_original", "manual_review"):
        return patch.copy()
    if mode == "safe_fill":
        return _restore_safe_fill(patch, mask)
    if mode == "gradient_restore":
        return _restore_gradient(patch, mask)
    if mode == "panel_restore":
        return _restore_panel(patch, mask)
    if mode == "advanced_inpaint":
        return _restore_inpaint(patch, mask, radius=8)
    # default: text_pixel_inpaint
    return _restore_inpaint(patch, mask, radius=3)


def _auto_mode(bg_type: str, risk_score: float) -> str:
    """Auto-select mode based on background type and risk."""
    if risk_score > 0.72:
        return ProcessingMode.manual_review.value

    mapping = {
        "solid": ProcessingMode.safe_fill.value,
        "gradient": ProcessingMode.gradient_restore.value,
        "panel": ProcessingMode.panel_restore.value,
        "photo": ProcessingMode.text_pixel_inpaint.value,
    }
    return mapping.get(bg_type, ProcessingMode.text_pixel_inpaint.value)


# ---------------------------------------------------------------------------
# Quality assessment
# ---------------------------------------------------------------------------

def assess_quality(original: np.ndarray, restored: np.ndarray, mask: np.ndarray) -> float:
    """
    Quality score [0, 1].
    Compares restored area against surrounding ring.
    Penalizes color mismatch, brightness jumps, and edge artifacts.
    """
    mask_bool = mask > 0
    if mask_bool.sum() == 0:
        return 1.0

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))
    dilated = cv2.dilate(mask, kernel)
    ring = (dilated > 0) & ~mask_bool

    if ring.sum() < 5:
        return 0.55

    ring_px = original[ring].reshape(-1, 3).astype(np.float32)
    rest_px = restored[mask_bool].reshape(-1, 3).astype(np.float32)

    # Color distance (normalised)
    color_diff = float(np.linalg.norm(
        np.mean(ring_px, axis=0) - np.mean(rest_px, axis=0)
    )) / (255.0 * np.sqrt(3))

    # Brightness difference
    bright_diff = abs(float(np.mean(ring_px)) - float(np.mean(rest_px))) / 255.0

    # Edge artifact check at mask boundary
    gray_restored = cv2.cvtColor(restored, cv2.COLOR_BGR2GRAY).astype(np.float32)
    lap = np.abs(cv2.Laplacian(gray_restored, cv2.CV_32F))
    k_sm = np.ones((3, 3), np.uint8)
    boundary = (cv2.dilate(mask, k_sm) - cv2.erode(mask, k_sm)) > 0
    edge_score = min(1.0, float(np.mean(lap[boundary])) / 60.0) if boundary.sum() > 0 else 0.0

    quality = 1.0 - (0.40 * color_diff + 0.40 * bright_diff + 0.20 * edge_score)
    return float(np.clip(quality, 0.0, 1.0))


# ---------------------------------------------------------------------------
# Color matching & blending
# ---------------------------------------------------------------------------

def color_match(original: np.ndarray, restored: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Nudge mean/std of restored pixels to match the surrounding ring.
    Applies a gentle correction (max ±50% std scaling).
    """
    mask_bool = mask > 0
    if mask_bool.sum() == 0:
        return restored

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))
    dilated = cv2.dilate(mask, kernel)
    ring = (dilated > 0) & ~mask_bool

    if ring.sum() < 5:
        return restored

    result = restored.copy().astype(np.float32)

    for c in range(3):
        src = restored[mask_bool, c].astype(np.float32)
        tgt = original[ring, c].astype(np.float32)

        src_mean, src_std = src.mean(), src.std()
        tgt_mean, tgt_std = tgt.mean(), tgt.std()

        if src_std > 1.0:
            scale = np.clip(tgt_std / (src_std + 1e-6), 0.5, 2.0)
            result[mask_bool, c] = (src - src_mean) * scale + tgt_mean
        else:
            result[mask_bool, c] = tgt_mean

    return np.clip(result, 0, 255).astype(np.uint8)


def feather_blend(
    original: np.ndarray,
    restored: np.ndarray,
    mask: np.ndarray,
    feather_radius: int = 7,
) -> np.ndarray:
    """Gaussian-feathered compositing of restored over original."""
    mf = mask.astype(np.float32) / 255.0
    ksize = feather_radius * 2 + 1
    mf = cv2.GaussianBlur(mf, (ksize, ksize), feather_radius / 2.5)
    mf = mf[:, :, np.newaxis]
    blended = original.astype(np.float32) * (1.0 - mf) + restored.astype(np.float32) * mf
    return np.clip(blended, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Block-level processing
# ---------------------------------------------------------------------------

def _process_block(
    result_img: np.ndarray,
    original_img: np.ndarray,
    block: TextBlock,
    final_mask: np.ndarray,
) -> Tuple[np.ndarray, dict]:
    H, W = original_img.shape[:2]
    x, y, bw, bh = block.bbox.x, block.bbox.y, block.bbox.w, block.bbox.h

    pad = max(bw, bh, 24)
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(W, x + bw + pad)
    y2 = min(H, y + bh + pad)

    patch = original_img[y1:y2, x1:x2].copy()
    local_mask = final_mask[y1:y2, x1:x2].copy()

    debug = {
        "block_id": block.id,
        "bg_type": None,
        "mode": block.mode.value,
        "quality_score": None,
        "rollback": False,
    }

    if local_mask.sum() == 0:
        block.restore_status = RestoreStatus.success
        return result_img, debug

    bg_type = classify_background(patch, local_mask)
    debug["bg_type"] = bg_type

    # Determine effective mode
    effective_mode = block.mode.value
    if effective_mode == ProcessingMode.text_pixel_inpaint.value:
        effective_mode = _auto_mode(bg_type, block.risk_score)
    debug["mode"] = effective_mode

    if effective_mode == ProcessingMode.manual_review.value:
        block.restore_status = RestoreStatus.manual_review
        return result_img, debug

    if effective_mode == ProcessingMode.keep_original.value:
        block.restore_status = RestoreStatus.success
        return result_img, debug

    try:
        restored_patch = restore_with_mode(patch, local_mask, effective_mode)
    except Exception as e:
        block.restore_status = RestoreStatus.failed
        debug["rollback"] = True
        return result_img, debug

    quality = assess_quality(patch, restored_patch, local_mask)
    debug["quality_score"] = round(quality, 3)

    if quality < QUALITY_THRESHOLD:
        block.restore_status = RestoreStatus.rollback
        debug["rollback"] = True
        return result_img, debug

    restored_patch = color_match(patch, restored_patch, local_mask)
    blended = feather_blend(patch, restored_patch, local_mask)

    result_img[y1:y2, x1:x2] = blended
    block.restore_status = RestoreStatus.success
    return result_img, debug


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def remove_text(session_dir: Path, blocks: List[TextBlock]) -> np.ndarray:
    """
    Quick global inpaint → clean_background.png
    (coarse removal; restore_background does the refined per-block work)
    """
    img = cv2.imread(str(session_dir / "original.png"))
    final_mask = cv2.imread(str(session_dir / "final_remove_mask.png"), cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise FileNotFoundError("original.png not found")
    if final_mask is None:
        raise FileNotFoundError("final_remove_mask.png not found")

    # Only inpaint pixels that belong to visible blocks
    active_mask = np.zeros_like(final_mask)
    H, W = img.shape[:2]
    for block in blocks:
        if block.visible and block.mode.value != ProcessingMode.keep_original.value:
            x, y, bw, bh = block.bbox.x, block.bbox.y, block.bbox.w, block.bbox.h
            x2, y2 = min(W, x + bw), min(H, y + bh)
            region = final_mask[y:y2, x:x2]
            active_mask[y:y2, x:x2] = cv2.bitwise_or(active_mask[y:y2, x:x2], region)

    clean = cv2.inpaint(img, active_mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
    cv2.imwrite(str(session_dir / "clean_background.png"), clean)

    for block in blocks:
        if block.mode.value != ProcessingMode.keep_original.value:
            block.restore_status = RestoreStatus.pending

    return clean


def restore_background(session_dir: Path, blocks: List[TextBlock]) -> np.ndarray:
    """
    Per-block refined restoration → restored_background.png
    """
    original = cv2.imread(str(session_dir / "original.png"))
    final_mask = cv2.imread(str(session_dir / "final_remove_mask.png"), cv2.IMREAD_GRAYSCALE)

    if original is None:
        raise FileNotFoundError("original.png not found")
    if final_mask is None:
        raise FileNotFoundError("final_remove_mask.png not found")

    result = original.copy()
    debug_list = []

    for block in blocks:
        if not block.visible:
            block.restore_status = RestoreStatus.success
            continue
        result, dbg = _process_block(result, original, block, final_mask)
        debug_list.append(dbg)

    cv2.imwrite(str(session_dir / "restored_background.png"), result)

    with open(session_dir / "block_debug.json", "w", encoding="utf-8") as f:
        json.dump(debug_list, f, indent=2, ensure_ascii=False)

    return result
