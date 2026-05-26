@echo off
title Calligraphy-Backend

set PYTHON=%LOCALAPPDATA%\Programs\Python\Python310\python.exe

if not exist "%PYTHON%" (
    echo ERROR: Python not found at %PYTHON%
    pause
    exit /b 1
)

cd /d "%~dp0backend"

echo ====================================
echo   Calligraphy App - Backend Server
echo ====================================
echo.
echo  Starting OCR server on port 8000...
echo  Close this window to stop
echo ====================================
echo.

"%PYTHON%" -m uvicorn main:app --host 0.0.0.0 --port 8000
echo.
echo Server stopped.
pause
