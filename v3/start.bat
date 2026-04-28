@echo off
echo ============================================
echo  AutoPPT v3 - Start
echo ============================================
echo.

echo [Backend]  http://localhost:8000 starting...
start "AutoPPT v3 - Backend" cmd /k "cd /d %~dp0backend && python main.py"

timeout /t 2 /nobreak > nul

echo [Frontend] http://localhost:3000 starting...
start "AutoPPT v3 - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================
echo  Both servers are running in separate windows.
echo  Opening http://localhost:3000 in 3 seconds...
echo  (Backend may take 5-10 sec on first run)
echo ============================================
echo.
echo  To stop: run stop.bat
echo.

timeout /t 3 /nobreak > nul
start http://localhost:3000

pause
