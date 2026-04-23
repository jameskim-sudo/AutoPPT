@echo off
chcp 65001 >nul
title AutoPPT

echo.
echo  =========================================
echo    AutoPPT - 이미지 to Editable PPTX
echo  =========================================
echo.

:: ── 현재 스크립트 위치를 프로젝트 루트로 설정 ──────────────────────────────
cd /d "%~dp0"

:: ── 가상환경 존재 여부 확인 및 최초 설치 ──────────────────────────────────
if not exist "backend\venv\Scripts\activate.bat" (
    echo [1/3] Python 가상환경 생성 중...
    python -m venv backend\venv
    if errorlevel 1 (
        echo [오류] Python 가상환경 생성 실패. Python 3.11+ 설치 여부를 확인하세요.
        pause
        exit /b 1
    )
    echo [2/3] 백엔드 패키지 설치 중 ^(최초 1회, 수 분 소요^)...
    call backend\venv\Scripts\activate.bat
    pip install -r backend\requirements.txt
    if errorlevel 1 (
        echo [오류] pip install 실패. requirements.txt를 확인하세요.
        pause
        exit /b 1
    )
) else (
    echo [확인] 가상환경 감지됨. 설치 단계 건너뜀.
)

:: ── node_modules 존재 여부 확인 및 최초 설치 ─────────────────────────────
if not exist "frontend\node_modules" (
    echo [3/3] 프론트엔드 패키지 설치 중 ^(최초 1회^)...
    cd frontend
    npm install --legacy-peer-deps
    if errorlevel 1 (
        echo [오류] npm install 실패.
        pause
        exit /b 1
    )
    cd ..
) else (
    echo [확인] node_modules 감지됨. 설치 단계 건너뜀.
)

echo.
echo  백엔드 서버 시작 중...
start "AutoPPT Backend" cmd /k "title AutoPPT-Backend && cd /d "%~dp0backend" && call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo  프론트엔드 서버 시작 중...
start "AutoPPT Frontend" cmd /k "title AutoPPT-Frontend && cd /d "%~dp0frontend" && npm run dev"

echo.
echo  서버가 준비될 때까지 잠시 기다리는 중 (8초)...
timeout /t 8 /nobreak >nul

echo  브라우저를 열고 있습니다...
start http://localhost:3000

echo.
echo  =========================================
echo   실행 완료!
echo   프론트엔드: http://localhost:3000
echo   백엔드 API: http://localhost:8000/docs
echo  =========================================
echo.
echo  이 창을 닫아도 서버는 계속 실행됩니다.
echo  서버를 종료하려면 stop.bat 을 실행하세요.
echo.
pause
