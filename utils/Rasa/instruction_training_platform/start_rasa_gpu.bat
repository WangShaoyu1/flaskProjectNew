@echo off
echo =========================================
echo Rasa GPU加速启动脚本 (Windows)
echo 专为RTX 3080Ti优化
echo =========================================

REM 设置GPU环境变量
set CUDA_VISIBLE_DEVICES=0
set TF_FORCE_GPU_ALLOW_GROWTH=true
set TF_GPU_ALLOCATOR=cuda_malloc_async
set TF_CPP_MIN_LOG_LEVEL=2
set TF_ENABLE_ONEDNN_OPTS=1
set PYTHONUNBUFFERED=1
set PYTHONOPTIMIZE=2
set RASA_TELEMETRY_ENABLED=false

echo 检查GPU状态...
nvidia-smi
if %errorlevel% neq 0 (
    echo 错误: 无法检测到NVIDIA GPU，请检查驱动安装
    pause
    exit /b 1
)

echo.
echo 启动Python GPU加速脚本...
python start_rasa_gpu.py

pause 