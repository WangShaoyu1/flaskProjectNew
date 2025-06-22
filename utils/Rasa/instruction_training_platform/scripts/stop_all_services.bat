@echo off
chcp 65001 >nul
echo ==============================================
echo    指令训练平台 - 停止所有服务
echo ==============================================
echo.

echo 正在停止所有相关服务...
echo.

:: 停止前端服务 (Node.js)
echo [1/4] 停止前端服务...
taskkill /f /im node.exe >nul 2>&1
if errorlevel 1 (
    echo ⚠️  未找到运行中的Node.js进程
) else (
    echo ✅ 前端服务已停止
)

:: 停止后端服务 (Python app.py)
echo [2/4] 停止后端服务...
for /f "tokens=2" %%i in ('netstat -ano ^| findstr :8081') do (
    taskkill /f /pid %%i >nul 2>&1
)
echo ✅ 后端服务已停止

:: 停止Rasa服务
echo [3/4] 停止Rasa服务...
for /f "tokens=2" %%i in ('netstat -ano ^| findstr :5005') do (
    taskkill /f /pid %%i >nul 2>&1
)
echo ✅ Rasa服务已停止

:: 停止其他Python进程（如果有的话）
echo [4/4] 清理其他相关进程...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

echo.
echo ==============================================
echo    所有服务已停止
echo ==============================================
echo.
echo 按任意键退出...
pause >nul 