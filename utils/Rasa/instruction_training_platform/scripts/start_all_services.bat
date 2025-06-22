@echo off
chcp 65001 >nul
title 指令训练平台 - 服务启动
echo ==============================================
echo    指令训练平台 - 顺序启动脚本
echo    启动顺序: Rasa → 后端 → 前端
echo ==============================================
echo.

:: 设置工作目录 (scripts文件夹的上级目录)
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\"
cd /d "%PROJECT_ROOT%"

:: 检查环境
echo [1/7] 检查运行环境...
echo.

echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境
    echo 请安装Python 3.8+并添加到PATH
    pause
    exit /b 1
)
echo ✅ Python环境检查通过

echo 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Node.js环境
    echo 请安装Node.js 14+并添加到PATH
    pause
    exit /b 1
)
echo ✅ Node.js环境检查通过

:: 检查项目结构和依赖
echo [2/7] 检查项目结构和依赖...
echo.

echo 检查后端虚拟环境...
if not exist "backend\venv\Scripts\activate.bat" (
    echo ❌ 错误: 未找到Python虚拟环境
    echo 请先在backend目录下创建虚拟环境:
    echo   cd backend
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)
echo ✅ 后端虚拟环境检查通过

echo 检查前端依赖...
if not exist "frontend\node_modules" (
    echo ❌ 错误: 未找到node_modules目录
    echo 请先在frontend目录下安装依赖:
    echo   cd frontend
    echo   npm install
    pause
    exit /b 1
)
echo ✅ 前端依赖检查通过

echo 检查Rasa启动脚本...
if not exist "scripts\start_rasa_simple.py" (
    echo ❌ 错误: 未找到Rasa启动脚本
    pause
    exit /b 1
)
echo ✅ Rasa启动脚本检查通过

:: 第一步: 启动Rasa服务
echo.
echo [3/7] 启动Rasa服务...
echo ==============================================
echo 正在启动Rasa服务，这可能需要一些时间...
echo 如果是第一次运行，可能需要训练模型
echo ==============================================
echo.

cd /d "%PROJECT_ROOT%"
echo 当前目录: %CD%
echo 执行命令: python scripts\start_rasa_simple.py
echo.

start /b python scripts\start_rasa_simple.py

:: 等待Rasa服务启动
echo 等待Rasa服务启动...
echo 注意: Rasa服务启动可能需要较长时间，特别是首次运行时
timeout /t 15 /nobreak >nul

:: 检查Rasa服务是否启动成功
echo.
echo 检查Rasa服务状态...
curl -s http://localhost:5005 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Rasa服务可能未完全启动，但继续下一步...
) else (
    echo ✅ Rasa服务启动成功 (端口: 5005)
)

:: 第二步: 启动后端服务
echo.
echo [4/7] 启动后端服务...
echo ==============================================
echo 正在启动后端服务...
echo ==============================================
echo.

cd /d "%PROJECT_ROOT%\backend"
echo 当前目录: %CD%
echo 激活虚拟环境...

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 错误: 无法激活虚拟环境
    pause
    exit /b 1
)

echo ✅ 虚拟环境激活成功
echo 启动后端应用...
echo 执行命令: python app.py
echo.

start /b python app.py

:: 等待后端服务启动
echo 等待后端服务启动...
timeout /t 8 /nobreak >nul

:: 检查后端服务状态
curl -s http://localhost:8081 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  后端服务可能未完全启动，但继续下一步...
) else (
    echo ✅ 后端服务启动成功 (端口: 8081)
)

:: 第三步: 启动前端服务
echo.
echo [5/7] 启动前端服务...
echo ==============================================
echo 正在启动前端服务...
echo ==============================================
echo.

cd /d "%PROJECT_ROOT%\frontend"
echo 当前目录: %CD%
echo 执行命令: npm start
echo.

start /b npm start

:: 等待前端服务启动
echo 等待前端服务启动...
timeout /t 10 /nobreak >nul

:: 检查前端服务状态
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  前端服务可能未完全启动
) else (
    echo ✅ 前端服务启动成功 (端口: 3000)
)

:: 显示服务状态
echo.
echo [6/7] 检查所有服务状态...
echo ==============================================
echo 服务状态检查:
echo.

echo 检查Rasa服务 (端口5005)...
curl -s http://localhost:5005 >nul 2>&1
if errorlevel 1 (
    echo   ❌ Rasa服务: 未响应
) else (
    echo   ✅ Rasa服务: 正常运行
)

echo 检查后端服务 (端口8081)...
curl -s http://localhost:8081 >nul 2>&1
if errorlevel 1 (
    echo   ❌ 后端服务: 未响应
) else (
    echo   ✅ 后端服务: 正常运行
)

echo 检查前端服务 (端口3000)...
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo   ❌ 前端服务: 未响应
) else (
    echo   ✅ 前端服务: 正常运行
)

:: 启动完成
echo.
echo [7/7] 启动完成！
echo ==============================================
echo    所有服务已启动，访问地址:
echo.
echo    🌐 前端界面: http://localhost:3000
echo    🔧 后端API:  http://localhost:8081
echo    📚 API文档:  http://localhost:8081/docs
echo    🤖 Rasa API: http://localhost:5005
echo ==============================================
echo.

set /p OPEN_BROWSER="是否打开前端界面? (y/n): "
if /i "%OPEN_BROWSER%"=="y" (
    echo 正在打开浏览器...
    start http://localhost:3000
)

echo.
echo 提示: 所有服务在后台运行
echo 要停止服务，请运行 stop_all_services.bat 或关闭相关进程
echo.
pause 