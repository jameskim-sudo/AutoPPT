# AutoPPT v2 — 이미지 픽셀 기반 텍스트 제거

bbox / OCR / protection mask **전혀 사용하지 않음.**  
이미지 픽셀 분석만으로 텍스트를 검출하고 제거하는 파이프라인.

## 파이프라인

```
이미지
  │
  ▼ STEP 1: Grayscale → Adaptive Threshold → Local Contrast
  │         Connected Component 분석 (작고 얇은 구조 = 텍스트 후보)
  │         → text_pixel_mask.png
  │
  ▼ STEP 2: HSV / LAB 색공간에서 저채도 + 어두운 영역 추출
  │         shape_mask AND color_mask 결합
  │
  ▼ STEP 3: Morphology Open/Close + 2차 CC 필터로 노이즈 제거
  │         → filtered_mask.png
  │
  ▼ STEP 4: cv2.inpaint (INPAINT_TELEA), dilation 1~2px만 적용
  │
  ▼ STEP 5: LAB 밝기 보정 + 경계 Gaussian blur
  │
  ▼ STEP 6: 결과 저장
            → clean_image.png
```

## 실행

```bash
# 패키지 설치 (최초 1회)
pip install -r requirements.txt

# 실행
python text_remover.py <input_image> [output_dir]

# 예시
python text_remover.py sample.png output
```

## 출력 파일

| 파일 | 설명 |
|------|------|
| `gray.png` | 그레이스케일 변환 결과 |
| `threshold.png` | Adaptive threshold 결과 |
| `text_pixel_mask.png` | Shape 기반 텍스트 픽셀 마스크 |
| `filtered_mask.png` | Color 필터 적용 후 최종 마스크 |
| `clean_image.png` | 텍스트 제거 완료 이미지 |

## 제한 사항 (의도된 것)

- bbox, polygon, OCR 좌표 **사용 안 함**
- protection mask **없음**
- 목표: "실제로 지워지는지 확인"하는 단계 — 완벽한 품질이 목표가 아님
- 최소 50% 이상 텍스트 픽셀 제거가 성공 기준

## 파일 구조

```
v2/
├── text_remover.py   # 메인 파이프라인
├── requirements.txt
├── README.md
└── output/           # 실행 결과 (gitignore)
```
