# AutoPPT

이미지를 분석하여 편집 가능한 PPTX로 변환하는 프로젝트입니다.  
버전별로 디렉토리가 구분되어 있습니다.

## 버전 구조

```
AutoPPT/
├── v1/   # 이미지 → Editable PPTX (OCR + Inpainting 파이프라인)
└── v2/   # 새 프롬프트 기반 구현 (진행 중)
```

## v1 — 이미지 → Editable PPTX

- **기술 스택**: FastAPI · Next.js · PaddleOCR · LaMa Inpainting · python-pptx
- **기능**: 이미지 업로드 → 텍스트 감지 → OCR 교정 → 인페인팅 → PPTX 생성
- **실행**: `v1/start.bat` (Windows) 또는 `v1/` 에서 `docker compose up`

## v2 — (New Prompt)

새로운 프롬프트로 구현 예정입니다.
