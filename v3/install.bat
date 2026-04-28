@echo off
echo ============================================
echo  AutoPPT v3 - Install
echo ============================================
echo.

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found.
    echo  Install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found

node --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found.
    echo  Install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js found

echo.
echo [1/4] Installing backend packages...
cd /d %~dp0backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Backend install failed.
    pause
    exit /b 1
)

echo.
echo [2/4] Installing PaddleOCR (Korean + English OCR)...
pip install paddlepaddle paddleocr
if %errorlevel% neq 0 (
    echo [WARN] PaddleOCR install failed. Will use MSER fallback.
)

echo.
echo [3/4] Installing frontend packages...
cd /d %~dp0frontend
npm install
if %errorlevel% neq 0 (
    echo [ERROR] Frontend install failed.
    pause
    exit /b 1
)

echo.
echo [4/4] Done!
echo ============================================
echo  Installation complete. Run start.bat next.
echo ============================================
pause
