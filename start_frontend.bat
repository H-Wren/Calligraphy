@echo off
title Calligraphy-Frontend

set PYTHON=%LOCALAPPDATA%\Programs\Python\Python310\python.exe

if not exist "%PYTHON%" (
    echo ERROR: Python not found
    pause
    exit /b 1
)

cd /d "%~dp0"

echo ====================================
echo   Calligraphy App - Frontend Server
echo ====================================
echo.
echo Open in browser:
echo   http://localhost:8080/frontend/
echo.
echo Close this window to stop
echo ====================================
echo.

"%PYTHON%" -m http.server 8080
echo.
echo Server stopped.
pause
