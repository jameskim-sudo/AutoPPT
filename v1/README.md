# AutoPPT v1 — 이미지 → Editable PPTX

이미지 파일에서 텍스트를 감지·인식한 뒤, 배경을 인페인팅으로 복원하고  
편집 가능한 `.pptx` 파일로 변환하는 웹 앱입니다.

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| Backend | FastAPI, PaddleOCR, LaMa Inpainting, python-pptx |
| Frontend | Next.js 16, Tailwind CSS |
| 실행 | Docker Compose / start.bat (Windows) |

## 파이프라인

```
이미지 업로드 → 텍스트 박스 감지 → OCR 교정 → 인페인팅 → PPTX 생성 → 다운로드
```

## 실행 방법

### Windows (권장)

```bat
start.bat
```

최초 실행 시 Python 가상환경 생성 및 패키지 설치가 자동으로 진행됩니다.

### Docker Compose

```bash
cd v1
docker compose up --build
```

- 프론트엔드: http://localhost:3000  
- 백엔드 API 문서: http://localhost:8000/docs

## 디렉토리 구조

```
v1/
├── backend/
│   ├── app/
│   │   ├── api/routes/    # upload, analyze, inpaint, generate_ppt, download
│   │   ├── services/      # ocr_service, inpaint_service, ppt_service
│   │   ├── models/        # Pydantic schemas
│   │   └── utils/         # color, coordinate, file, image_io helpers
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── app/           # Next.js App Router
│       ├── components/    # UI 컴포넌트
│       ├── hooks/         # useImageProcessor
│       └── utils/         # api, canvas
├── docker-compose.yml
├── start.bat
└── stop.bat
```
