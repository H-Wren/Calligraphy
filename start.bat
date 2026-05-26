@echo off
title 书法识文 - 一键启动
cd /d "%~dp0"

set PYTHON=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
if not exist "%PYTHON%" (
    echo 找不到 Python，请检查安装路径
    pause
    exit /b 1
)

echo ====================================
echo   书法识文 App - 启动中...
echo ====================================
echo.

:: 启动后端（新窗口）
start "书法识文-后端" "%PYTHON%" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

:: 等后端启动
cd /d "%~dp0backend"
echo 正在启动后端服务...
timeout /t 3 /nobreak >nul

:: 启动前端（新窗口）
cd /d "%~dp0"
start "书法识文-前端" "%PYTHON%" -m http.server 8081

echo.
echo 后端服务已启动: http://localhost:8000
echo 前端页面: http://localhost:8081/frontend/
echo.
echo 请在浏览器中打开 http://localhost:8081/frontend/
echo 关闭本窗口可停止所有服务
echo ====================================
echo.
pause
