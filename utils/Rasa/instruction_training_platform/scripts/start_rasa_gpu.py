#!/usr/bin/env python3
"""
Rasa GPU加速启动脚本
专为RTX 3080Ti优化，启用CUDA加速
"""

import os
import sys
import subprocess
import time
import psutil
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_gpu_environment():
    """设置GPU环境变量"""
    gpu_env = {
        # 启用GPU加速
        'CUDA_VISIBLE_DEVICES': '0',
        'TF_FORCE_GPU_ALLOW_GROWTH': 'true',
        'TF_GPU_ALLOCATOR': 'cuda_malloc_async',
        
        # 优化TensorFlow
        'TF_CPP_MIN_LOG_LEVEL': '2',  # 减少TF日志
        'TF_ENABLE_ONEDNN_OPTS': '1',  # 启用oneDNN优化
        'TF_XLA_FLAGS': '--tf_xla_enable_xla_devices',  # 启用XLA
        
        # 修复TensorFlow 2.12.0的NoneType错误
        'TF_ENABLE_DEPRECATION_WARNINGS': '0',  # 禁用弃用警告
        'TF_DISABLE_MKL': '1',  # 禁用MKL以避免某些兼容性问题
        'TF_FORCE_UNIFIED_MEMORY': '1',  # 强制统一内存管理
        
        # 优化Python
        'PYTHONUNBUFFERED': '1',
        'PYTHONOPTIMIZE': '2',
        'PYTHONWARNINGS': 'ignore::DeprecationWarning',  # 忽略弃用警告
        
        # Rasa优化
        'RASA_TELEMETRY_ENABLED': 'false',  # 关闭遥测
        'RASA_PRO_LICENSE': '',  # 如果有Pro许可证
    }
    
    for key, value in gpu_env.items():
        os.environ[key] = value
        logger.info(f"设置环境变量: {key}={value}")

def check_gpu_availability():
    """检查GPU可用性"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("GPU检测成功:")
            print(result.stdout)
            return True
        else:
            logger.error("GPU检测失败")
            return False
    except FileNotFoundError:
        logger.error("nvidia-smi未找到，请安装NVIDIA驱动")
        return False

def check_memory():
    """检查系统内存"""
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024**3)
    available_gb = memory.available / (1024**3)
    
    logger.info(f"系统内存: {memory_gb:.1f}GB, 可用: {available_gb:.1f}GB")
    
    if available_gb < 4:
        logger.warning("可用内存不足4GB，可能影响性能")
        return False
    return True

def kill_existing_rasa():
    """关闭现有的Rasa进程"""
    killed = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'rasa' in proc.info['name'].lower():
                logger.info(f"关闭现有Rasa进程: PID {proc.info['pid']}")
                proc.kill()
                killed = True
            elif proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline']).lower()
                if 'rasa run' in cmdline or 'rasa-server' in cmdline:
                    logger.info(f"关闭现有Rasa进程: PID {proc.info['pid']}")
                    proc.kill()
                    killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if killed:
        time.sleep(2)  # 等待进程完全关闭

def start_rasa_server():
    """启动Rasa服务器"""
    # 切换到rasa目录 (scripts文件夹的上级目录下的rasa)
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    rasa_dir = os.path.join(project_root, 'rasa')
    os.chdir(rasa_dir)
    
    # 构建启动命令
    cmd = [
        sys.executable, '-m', 'rasa', 'run',
        '--enable-api',
        '--cors', '*',
        '--port', '5005',
        '--endpoints', 'endpoints.yml',
        '--credentials', 'credentials.yml'
    ]
    
    logger.info(f"启动命令: {' '.join(cmd)}")
    logger.info("正在启动Rasa服务器 (GPU加速模式)...")
    
    try:
        # 启动进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 监控启动过程
        startup_timeout = 120  # 2分钟超时
        start_time = time.time()
        server_ready = False
        
        while time.time() - start_time < startup_timeout:
            line = process.stdout.readline()
            if line:
                print(line.strip())
                if "Rasa server is up and running" in line or "Starting Rasa server" in line:
                    server_ready = True
                    break
            
            if process.poll() is not None:
                logger.error("Rasa服务器启动失败")
                return False
        
        if server_ready:
            logger.info("Rasa服务器启动成功!")
            logger.info("服务地址: http://localhost:5005")
            logger.info("API文档: http://localhost:5005/docs")
            
            # 继续监控输出
            try:
                while True:
                    line = process.stdout.readline()
                    if line:
                        print(line.strip())
                    elif process.poll() is not None:
                        break
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在关闭服务器...")
                process.terminate()
                process.wait()
                
        else:
            logger.error("Rasa服务器启动超时")
            process.terminate()
            return False
            
    except Exception as e:
        logger.error(f"启动Rasa服务器失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("Rasa GPU加速启动脚本")
    print("专为RTX 3080Ti优化")
    print("=" * 60)
    
    # 检查GPU
    if not check_gpu_availability():
        logger.error("GPU不可用，请检查NVIDIA驱动和CUDA安装")
        return False
    
    # 检查内存
    if not check_memory():
        logger.warning("内存不足，但将继续启动")
    
    # 设置GPU环境
    setup_gpu_environment()
    
    # 关闭现有进程
    kill_existing_rasa()
    
    # 启动服务器
    success = start_rasa_server()
    
    if success:
        logger.info("Rasa服务器运行完成")
    else:
        logger.error("启动失败")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n用户中断，退出程序")
        sys.exit(0)
    except Exception as e:
        logger.error(f"未知错误: {e}")
        sys.exit(1) 