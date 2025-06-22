#!/usr/bin/env python3
"""
Rasa简化启动脚本
去掉复杂的GPU配置，专注于基本启动
"""

import os
import sys
import subprocess
import time
import psutil
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_basic_environment():
    """设置基本环境变量"""
    basic_env = {
        # 基本Python优化
        'PYTHONUNBUFFERED': '1',
        
        # Rasa配置
        'RASA_TELEMETRY_ENABLED': 'false',  # 关闭遥测
    }
    
    for key, value in basic_env.items():
        os.environ[key] = value
        logger.info(f"设置环境变量: {key}={value}")

def kill_existing_rasa():
    """关闭现有的Rasa进程"""
    killed = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline']:
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
    if not os.path.exists(rasa_dir):
        logger.error(f"Rasa目录不存在: {rasa_dir}")
        return False
    
    os.chdir(rasa_dir)
    logger.info(f"切换到Rasa目录: {os.getcwd()}")
    
    # 检查必要文件
    required_files = ['config.yml', 'data/domain.yml', 'data/nlu.yml']
    for file in required_files:
        if not os.path.exists(file):
            logger.error(f"缺少必要文件: {file}")
            return False
    
    # 构建启动命令 - 简化版
    cmd = [
        sys.executable, '-m', 'rasa', 'run',
        '--enable-api',
        '--cors', '*',
        '--port', '5005',
        '--endpoints', 'endpoints.yml'
    ]
    
    logger.info(f"启动命令: {' '.join(cmd)}")
    logger.info("正在启动Rasa服务器...")
    
    try:
        # 启动进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # 等待一段时间让服务启动
        time.sleep(5)
        
        # 检查进程是否还在运行
        if process.poll() is None:
            logger.info("Rasa服务器启动成功!")
            logger.info("服务地址: http://localhost:5005")
            
            # 让进程在后台继续运行
            return True
        else:
            # 获取错误信息
            stdout, stderr = process.communicate()
            logger.error("Rasa服务器启动失败")
            if stdout:
                logger.error(f"标准输出: {stdout}")
            if stderr:
                logger.error(f"错误输出: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"启动Rasa服务器失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("Rasa简化启动脚本")
    print("=" * 50)
    
    # 设置基本环境
    setup_basic_environment()
    
    # 关闭现有进程
    kill_existing_rasa()
    
    # 启动服务器
    success = start_rasa_server()
    
    if success:
        logger.info("Rasa服务器启动成功，在后台运行")
        print("\n✅ Rasa服务启动成功!")
        print("🌐 服务地址: http://localhost:5005")
        print("📚 API文档: http://localhost:5005/docs")
        print("\n服务正在后台运行...")
    else:
        logger.error("启动失败")
        print("\n❌ Rasa服务启动失败!")
        return False
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n收到中断信号，退出...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序异常: {e}")
        sys.exit(1) 