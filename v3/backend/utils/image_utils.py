from pathlib import Path
import cv2
import numpy as np
from PIL import Image


def read_image(path: Path) -> np.ndarray:
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    return img


def save_image(img: np.ndarray, path: Path) -> None:
    cv2.imwrite(str(path), img)


def get_image_size(path: Path) -> tuple[int, int]:
    """Returns (width, height)."""
    with Image.open(path) as im:
        return im.size


def normalize_to_png(src: Path, dst: Path) -> None:
    """Convert any image format to PNG."""
    with Image.open(src) as im:
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        im.save(dst, "PNG")


def mask_to_preview(mask: np.ndarray, color: tuple = (255, 0, 0), alpha: float = 0.5) -> np.ndarray:
    """Create a colored RGBA preview of a binary mask."""
    h, w = mask.shape[:2]
    preview = np.zeros((h, w, 4), dtype=np.uint8)
    mask_bool = mask > 0
    preview[mask_bool] = [*color, int(255 * alpha)]
    return preview


def create_composite_preview(base: np.ndarray, mask: np.ndarray,
                              color: tuple = (255, 80, 80), alpha: float = 0.4) -> np.ndarray:
    """Overlay mask on base image."""
    result = base.copy().astype(np.float32)
    mask_bool = mask > 0
    for c, val in enumerate(color[::-1]):  # BGR
        result[mask_bool, c] = result[mask_bool, c] * (1 - alpha) + val * alpha
    return result.astype(np.uint8)
