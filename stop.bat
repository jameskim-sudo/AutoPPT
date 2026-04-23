@echo off
chcp 65001 >nul
title AutoPPT - 서버 종료

echo AutoPPT 서버를 종료합니다...

:: uvicorn 프로세스 종료
taskkill /f /fi "WindowTitle eq AutoPPT-Backend*" >nul 2>&1
taskkill /f /im "uvicorn.exe" >nul 2>&1

:: next dev 프로세스 종료
taskkill /f /fi "WindowTitle eq AutoPPT-Frontend*" >nul 2>&1
taskkill /f /im "node.exe" /fi "WINDOWTITLE eq AutoPPT*" >nul 2>&1

echo 서버가 종료되었습니다.
timeout /t 2 /nobreak >nul
