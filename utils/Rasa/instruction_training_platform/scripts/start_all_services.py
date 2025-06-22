#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令训练平台 - 一键启动脚本
按顺序启动后端服务、Rasa服务和前端服务
"""

import os
import sys
import time
import subprocess
import platform
import webbrowser
from pathlib import Path


def print_banner():
    """打印启动横幅"""
    print("=" * 50)
    print("    指令训练平台 - 一键启动脚本")
    print("=" * 50)
    print()


def check_command(command):
    """检查命令是否可用"""
    try:
        subprocess.run([command, "--version"],
                       capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def wait_for_service(port, service_name, timeout=30):
    """等待服务启动"""
    print(f"等待{service_name}启动完成...")
    import socket
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                print(f"✅ {service_name}启动成功 (端口: {port})")
                return True
        except:
            pass
        time.sleep(2)

    print(f"⚠️  {service_name}启动超时，但继续执行...")
    return False


def start_service(command, title, cwd=None, shell=False):
    """启动服务"""
    try:
        if platform.system() == "Windows":
            # Windows下使用start命令在新窗口中启动
            if isinstance(command, list):
                command = " && ".join(command)
            subprocess.Popen(f'start "{title}" cmd /k "{command}"',
                             shell=True, cwd=cwd)
        else:
            # Linux/Mac下使用nohup在后台启动
            if isinstance(command, str):
                command = command.split()
            subprocess.Popen(command, cwd=cwd)
        return True
    except Exception as e:
        print(f"❌ 启动{title}失败: {e}")
        return False


def main():
    """主函数"""
    print_banner()

    # 获取项目根目录 (scripts文件夹的上级目录)
    project_root = Path(__file__).parent.parent.absolute()
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"
    rasa_dir = project_root / "rasa"

    print(f"项目根目录: {project_root}")
    print()

    # 检查环境
    print("[1/6] 检查运行环境...")

    if not check_command("python"):
        print("❌ 错误: 未找到Python环境")
        sys.exit(1)
    print("✅ Python环境检查通过")

    if not check_command("node"):
        print("❌ 错误: 未找到Node.js环境")
        sys.exit(1)
    print("✅ Node.js环境检查通过")

    # 检查目录结构
    print("\n[2/6] 检查项目结构...")

    if not backend_dir.exists():
        print("❌ 错误: 未找到backend目录")
        sys.exit(1)

    if not frontend_dir.exists():
        print("❌ 错误: 未找到frontend目录")
        sys.exit(1)

    if not rasa_dir.exists():
        print("❌ 错误: 未找到rasa目录")
        sys.exit(1)

    # 检查虚拟环境
    if platform.system() == "Windows":
        venv_activate = backend_dir / "venv" / "Scripts" / "activate.bat"
    else:
        venv_activate = backend_dir / "venv" / "bin" / "activate"

    if not venv_activate.exists():
        print("❌ 错误: 未找到Python虚拟环境")
        print("请先在backend目录下创建虚拟环境并安装依赖")
        sys.exit(1)

    # 检查Node.js依赖
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("❌ 错误: 未找到node_modules目录")
        print("请先在frontend目录下运行: npm install")
        sys.exit(1)

    print("✅ 项目结构检查通过")

    # 启动后端服务
    print("\n[3/6] 启动后端服务...")
    if platform.system() == "Windows":
        backend_cmd = f"cd /d {backend_dir} && venv\\Scripts\\activate.bat && python app.py"
    else:
        backend_cmd = f"cd {backend_dir} && source venv/bin/activate && python app.py"

    if start_service(backend_cmd, "后端服务", cwd=backend_dir):
        print("✅ 后端服务启动中... (端口: 8081)")
        time.sleep(8)  # 给后端服务一些启动时间
    else:
        print("❌ 后端服务启动失败")
        sys.exit(1)

    # 启动Rasa服务
    print("\n[4/6] 启动Rasa服务...")
    rasa_cmd = f"cd /d {project_root} && python scripts/start_rasa_simple.py"

    if start_service(rasa_cmd, "Rasa服务", cwd=project_root):
        print("✅ Rasa服务启动中... (端口: 5005)")
        time.sleep(12)  # 给Rasa服务更多启动时间
    else:
        print("❌ Rasa服务启动失败")
        sys.exit(1)

    # 启动前端服务
    print("\n[5/6] 启动前端服务...")
    frontend_cmd = f"cd /d {frontend_dir} && npm start"

    if start_service(frontend_cmd, "前端服务", cwd=frontend_dir):
        print("✅ 前端服务启动中... (端口: 3000)")
        time.sleep(8)  # 给前端服务一些启动时间
    else:
        print("❌ 前端服务启动失败")
        sys.exit(1)

    # 完成启动
    print("\n[6/6] 所有服务启动完成！")
    print()
    print("=" * 50)
    print("    服务访问地址:")
    print("    前端界面: http://localhost:3000")
    print("    后端API:  http://localhost:8081")
    print("    API文档:  http://localhost:8081/docs")
    print("    Rasa API: http://localhost:5005")
    print("=" * 50)
    print()

    # 询问是否打开浏览器
    try:
        response = input("是否自动打开前端界面? (y/n): ").lower().strip()
        if response in ['y', 'yes', '是', '']:
            print("正在打开浏览器...")
            webbrowser.open('http://localhost:3000')
    except KeyboardInterrupt:
        print("\n程序被中断")

    print("\n所有服务已启动，可以开始使用系统了！")
    print("提示: 关闭此窗口不会停止服务，如需停止服务请分别关闭各服务窗口")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 启动过程中发生错误: {e}")
        sys.exit(1)
