"""
한글/유니코드 경로 호환 이미지 I/O 유틸리티

cv2.imread / cv2.imwrite 는 Windows에서 비ASCII 경로를 지원하지 않는다.
np.fromfile + cv2.imdecode / cv2.imencode + ndarray.tofile 로 우회한다.
"""

import numpy as np
import cv2
from pathlib import Path


def imread(path: str) -> np.ndarray:
    """
    유니코드/한글 경로를 지원하는 이미지 읽기.
    실패 시 None 대신 ValueError를 발생시킨다.
    """
    buf = np.fromfile(path, dtype=np.uint8)
    if buf.size == 0:
        raise ValueError(f"이미지 파일이 비어 있습니다: {path}")
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"이미지를 디코딩할 수 없습니다: {path}")
    return img


def imwrite(path: str, img: np.ndarray, ext: str = ".png") -> None:
    """
    유니코드/한글 경로를 지원하는 이미지 쓰기.
    """
    suffix = Path(path).suffix or ext
    ok, buf = cv2.imencode(suffix, img)
    if not ok:
        raise IOError(f"이미지 인코딩 실패: {path}")
    buf.tofile(path)
