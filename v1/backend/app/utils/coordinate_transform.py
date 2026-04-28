"""
좌표 변환 유틸리티

이미지 픽셀 좌표 → PPT EMU(English Metric Units) 좌표 변환

PPT 단위:
  1 inch = 914400 EMU
  1 pt   = 12700  EMU
  1 cm   = 360000 EMU

변환 공식:
  ppt_x = bbox_x / image_width  * slide_width_emu
  ppt_y = bbox_y / image_height * slide_height_emu
  ppt_w = bbox_w / image_width  * slide_width_emu
  ppt_h = bbox_h / image_height * slide_height_emu
"""

from pptx.util import Inches, Pt, Emu

# 기본 슬라이드 너비 (인치 단위, 13.33인치 = 와이드스크린 표준)
BASE_SLIDE_WIDTH_INCHES = 13.33
BASE_SLIDE_WIDTH_EMU = int(BASE_SLIDE_WIDTH_INCHES * 914400)


def calc_slide_dimensions(image_width: int, image_height: int) -> tuple[int, int]:
    """
    이미지 비율과 동일한 슬라이드 크기(EMU)를 반환한다.

    Args:
        image_width:  원본 이미지 너비 (px)
        image_height: 원본 이미지 높이 (px)

    Returns:
        (slide_width_emu, slide_height_emu)
    """
    aspect = image_height / image_width
    slide_w = BASE_SLIDE_WIDTH_EMU
    slide_h = int(slide_w * aspect)
    return slide_w, slide_h


def px_to_emu(px: float, image_dim: int, slide_dim_emu: int) -> int:
    """
    픽셀 값을 EMU로 변환한다.

    Args:
        px:           변환할 픽셀 값
        image_dim:    해당 축의 이미지 크기 (px)
        slide_dim_emu: 해당 축의 슬라이드 크기 (EMU)

    Returns:
        EMU 정수값
    """
    if image_dim == 0:
        return 0
    return int(px / image_dim * slide_dim_emu)


def bbox_to_emu(
    x: float,
    y: float,
    w: float,
    h: float,
    image_width: int,
    image_height: int,
    slide_width_emu: int,
    slide_height_emu: int,
) -> tuple[int, int, int, int]:
    """
    bounding box 픽셀 좌표를 EMU로 일괄 변환한다.

    Returns:
        (x_emu, y_emu, w_emu, h_emu)
    """
    x_emu = px_to_emu(x, image_width, slide_width_emu)
    y_emu = px_to_emu(y, image_height, slide_height_emu)
    w_emu = px_to_emu(w, image_width, slide_width_emu)
    h_emu = px_to_emu(h, image_height, slide_height_emu)
    return x_emu, y_emu, w_emu, h_emu


def estimate_font_size_pt(
    bbox_h_px: float,
    image_height: int,
    slide_height_emu: int,
    line_count: int = 1,
) -> float:
    """
    bounding box 높이(픽셀)로부터 폰트 크기(pt)를 추정한다.

    변환 로직:
      1. bbox_h_px → slide_h_emu (비율 변환)
      2. slide_h_emu → inch (÷ 914400)
      3. inch → pt (× 72)
      4. 라인 수로 나누기 + 패딩 보정 계수 적용

    Args:
        bbox_h_px:       bounding box 높이 (픽셀)
        image_height:    원본 이미지 높이 (픽셀)
        slide_height_emu: 슬라이드 높이 (EMU)
        line_count:      텍스트 줄 수 (기본 1)

    Returns:
        추정 폰트 크기 (pt)
    """
    h_emu = px_to_emu(bbox_h_px, image_height, slide_height_emu)
    h_inch = h_emu / 914400
    h_pt = h_inch * 72
    # 한 줄당 높이 = 전체 높이 / 줄 수
    # 줄 높이의 약 72%가 실제 글자 크기 (ascender+descender 제외)
    per_line_pt = (h_pt / max(1, line_count)) * 0.72
    # 최소 6pt, 최대 144pt로 클램핑
    return round(max(6.0, min(144.0, per_line_pt)), 1)
