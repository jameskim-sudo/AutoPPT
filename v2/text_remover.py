"""
v2 — 이미지 픽셀 기반 텍스트 제거 파이프라인

bbox / OCR / protection mask 전혀 사용하지 않음.
이미지 픽셀 분석만으로 텍스트를 검출하고 제거한다.

사용법:
    python text_remover.py <input_image> [output_dir]

출력 (output_dir, 기본값 ./output):
    gray.png              — 그레이스케일 변환 결과
    threshold.png         — adaptive threshold 결과
    text_pixel_mask.png   — shape 기반 텍스트 픽셀 마스크
    filtered_mask.png     — color 필터 적용 후 최종 마스크
    clean_image.png       — 텍스트 제거 완료 이미지
"""

import sys
import os
import cv2
import numpy as np
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: 텍스트 픽셀 검출 (shape 기반)
# ─────────────────────────────────────────────────────────────────────────────

def detect_text_pixels_by_shape(gray: np.ndarray) -> np.ndarray:
    """
    adaptive threshold + connected component 분석으로
    얇고 작은 글자 모양 구성요소를 추출한다.
    """
    h, w = gray.shape

    # adaptive threshold — 글자처럼 작은 local 고대비 영역 포착
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=15,
        C=8,
    )

    # local contrast map — 주변과 밝기 차이가 큰 곳만 남김
    blur = cv2.GaussianBlur(gray, (15, 15), 0)
    contrast = cv2.absdiff(gray, blur)
    _, contrast_mask = cv2.threshold(contrast, 12, 255, cv2.THRESH_BINARY)

    # shape mask: threshold AND contrast 둘 다 만족해야 함
    shape_mask = cv2.bitwise_and(thresh, contrast_mask)

    # connected component 분석 — 글자처럼 작은 component만 선택
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        shape_mask, connectivity=8
    )

    image_area = h * w
    text_mask = np.zeros_like(gray)

    for i in range(1, num_labels):  # 0은 배경
        area = stats[i, cv2.CC_STAT_AREA]
        cw = stats[i, cv2.CC_STAT_WIDTH]
        ch = stats[i, cv2.CC_STAT_HEIGHT]

        if area == 0:
            continue

        aspect = max(cw, ch) / max(min(cw, ch), 1)
        fill_ratio = area / max(cw * ch, 1)

        # 필터 조건
        # 너무 작은 노이즈 제거 (3픽셀 미만)
        if area < 3:
            continue
        # 이미지 전체 면적의 2% 넘는 큰 덩어리 = 아이콘/박스 → 제거
        if area > image_area * 0.02:
            continue
        # 가로세로가 너무 정사각형이고 채움률이 낮으면 선/박스 → 제거
        if aspect < 1.3 and fill_ratio < 0.25:
            continue

        text_mask[labels == i] = 255

    return thresh, text_mask


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 & 3: 색상 기반 필터링 + 노이즈 제거
# ─────────────────────────────────────────────────────────────────────────────

def filter_by_color(image_bgr: np.ndarray, shape_mask: np.ndarray) -> np.ndarray:
    """
    HSV + LAB 색공간에서 텍스트 색상 특징(저채도·고대비)을 추출해
    shape_mask와 AND 결합 후 morphology로 정제한다.
    """
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)

    # 저채도 영역 (S 채널 < 80 → 회색/검정/흰색 계열)
    _, s_ch, _ = cv2.split(hsv)
    _, low_sat_mask = cv2.threshold(s_ch, 80, 255, cv2.THRESH_BINARY_INV)

    # LAB L채널 기반 어두운 영역 (L < 180 → 밝지 않은 픽셀)
    l_ch, _, _ = cv2.split(lab)
    _, dark_mask = cv2.threshold(l_ch, 200, 255, cv2.THRESH_BINARY_INV)

    # 색상 마스크: 저채도 OR 어두운 영역 — 최대한 포용적으로
    color_mask = cv2.bitwise_or(low_sat_mask, dark_mask)

    # shape + color 결합
    combined = cv2.bitwise_and(shape_mask, color_mask)

    # morphology 정제 — 글자 획 사이 미세 빈틈 메우기
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel_close)

    # 작은 노이즈 제거 (open)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel_open)

    # 2차 connected component 필터 — 극히 작은 점 제거
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        combined, connectivity=8
    )
    filtered = np.zeros_like(combined)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= 5:
            filtered[labels == i] = 255

    return filtered


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: inpaint
# ─────────────────────────────────────────────────────────────────────────────

def inpaint_text(image_bgr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    mask 영역을 cv2.inpaint (Telea) 로 복원한다.
    dilation 1~2px만 적용해 과도한 번짐 방지.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated_mask = cv2.dilate(mask, kernel, iterations=1)

    result = cv2.inpaint(image_bgr, dilated_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: 색상 보정
# ─────────────────────────────────────────────────────────────────────────────

def color_correction(original: np.ndarray, inpainted: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    inpaint 결과에서 mask 영역의 밝기/채도를 주변 배경에 맞게 보정하고
    경계에 Gaussian blur를 적용해 자연스럽게 만든다.
    """
    # mask 경계 부근 (dilation 10px) 에서 배경 샘플링
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
    dilated = cv2.dilate(mask, kernel, iterations=1)
    bg_region = cv2.bitwise_and(dilated, cv2.bitwise_not(mask))

    if bg_region.sum() == 0:
        return inpainted  # 배경 샘플 없으면 그대로 반환

    # LAB 색공간에서 밝기(L) 보정
    orig_lab = cv2.cvtColor(original, cv2.COLOR_BGR2LAB).astype(np.float32)
    inp_lab = cv2.cvtColor(inpainted, cv2.COLOR_BGR2LAB).astype(np.float32)

    bg_mask_bool = bg_region > 0

    if bg_mask_bool.sum() == 0:
        return inpainted

    orig_l_mean = orig_lab[:, :, 0][bg_mask_bool].mean()
    inp_l_mean = inp_lab[:, :, 0][bg_mask_bool].mean()

    l_shift = orig_l_mean - inp_l_mean

    mask_bool = mask > 0
    inp_lab[:, :, 0][mask_bool] = np.clip(
        inp_lab[:, :, 0][mask_bool] + l_shift, 0, 255
    )

    corrected = cv2.cvtColor(inp_lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

    # 경계 자연화: mask 경계에만 작은 Gaussian blur 적용
    blur_radius = 5
    blurred = cv2.GaussianBlur(corrected, (blur_radius * 2 + 1, blur_radius * 2 + 1), 0)

    # 경계 마스크 (dilation - erosion)
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    eroded = cv2.erode(mask, kernel_small, iterations=1)
    border = cv2.bitwise_and(mask, cv2.bitwise_not(eroded))

    border_bool = border > 0
    corrected[border_bool] = blurred[border_bool]

    return corrected


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6: 메인 파이프라인
# ─────────────────────────────────────────────────────────────────────────────

def remove_text(input_path: str, output_dir: str = "output") -> dict[str, str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    image = cv2.imread(input_path)
    if image is None:
        raise FileNotFoundError(f"이미지를 읽을 수 없습니다: {input_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # STEP 1: shape 기반 텍스트 픽셀 검출
    print("[1/5] 텍스트 픽셀 검출 중 (adaptive threshold + connected components)...")
    thresh, shape_mask = detect_text_pixels_by_shape(gray)

    # STEP 2 & 3: 색상 필터 + 노이즈 정제
    print("[2/5] 색상 기반 필터링 및 노이즈 제거 중...")
    filtered_mask = filter_by_color(image, shape_mask)

    # STEP 4: inpaint
    print("[3/5] inpaint 처리 중 (cv2.INPAINT_TELEA)...")
    inpainted = inpaint_text(image, filtered_mask)

    # STEP 5: 색상 보정
    print("[4/5] 색상 보정 중...")
    clean = color_correction(image, inpainted, filtered_mask)

    # STEP 6: 디버그 파일 저장
    print("[5/5] 결과 저장 중...")
    outputs = {
        "gray":             os.path.join(output_dir, "gray.png"),
        "threshold":        os.path.join(output_dir, "threshold.png"),
        "text_pixel_mask":  os.path.join(output_dir, "text_pixel_mask.png"),
        "filtered_mask":    os.path.join(output_dir, "filtered_mask.png"),
        "clean_image":      os.path.join(output_dir, "clean_image.png"),
    }

    cv2.imwrite(outputs["gray"],            gray)
    cv2.imwrite(outputs["threshold"],       thresh)
    cv2.imwrite(outputs["text_pixel_mask"], shape_mask)
    cv2.imwrite(outputs["filtered_mask"],   filtered_mask)
    cv2.imwrite(outputs["clean_image"],     clean)

    # 통계 출력
    total_pixels = filtered_mask.size
    text_pixels = int((filtered_mask > 0).sum())
    coverage = text_pixels / total_pixels * 100
    print(f"\n  텍스트 픽셀 커버리지: {text_pixels:,} / {total_pixels:,} px ({coverage:.2f}%)")
    print(f"  출력 디렉토리: {os.path.abspath(output_dir)}\n")

    for name, path in outputs.items():
        print(f"  [{name}] → {path}")

    return outputs


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python text_remover.py <input_image> [output_dir]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"

    print(f"\n  입력: {input_path}")
    print(f"  출력 디렉토리: {output_dir}\n")

    remove_text(input_path, output_dir)
