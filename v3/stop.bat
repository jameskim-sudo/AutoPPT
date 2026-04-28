@echo off
echo ============================================
echo  AutoPPT v3 - Stop
echo ============================================

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do (
    taskkill /f /pid %%a > nul 2>&1
)
echo [OK] Backend (8000) stopped

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000 "') do (
    taskkill /f /pid %%a > nul 2>&1
)
echo [OK] Frontend (3000) stopped

echo.
echo Done.
timeout /t 2 /nobreak > nul
