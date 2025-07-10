#!/usr/bin/env python3
"""
智能对话训练平台 - 分标签页启动脚本 (Python版本)
支持Windows Terminal标签页启动，跨平台兼容
每个服务在独立标签页中显示详细日志
"""

import os
import sys
import subprocess
import platform
import time
import shutil
import signal
import json
from pathlib import Path

class PlatformTabsStarter:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.base_dir = self.script_dir.parent
        self.system = platform.system()
        self.processes = []
        
    def print_banner(self):
        """打印启动横幅"""
        print("\n" + "=" * 60)
        print("🚀 智能对话训练平台 v2.0.0 - 分标签页启动")
        print("=" * 60)
        print("📋 Python版本 - 跨平台支持")
        print("🎯 分标签页显示各服务详细日志")
        print("🔧 智能环境检查和故障诊断")
        print("=" * 60)
        print()
        
    def check_environment(self):
        """检查运行环境"""
        print("🔍 检查运行环境...")
        print()
        
        # 检查操作系统
        print(f"💻 操作系统: {self.system} {platform.release()}")
        print(f"🐍 Python版本: {sys.version}")
        print()
        
        # 检查Windows Terminal (仅Windows)
        if self.system == "Windows":
            wt_available = shutil.which("wt") is not None
            if wt_available:
                print("✅ Windows Terminal 已安装")
                print("🎯 支持分标签页启动")
            else:
                print("❌ Windows Terminal 未找到")
                print("💡 建议安装Windows Terminal以获得更好的体验")
                print("🔄 将使用传统方式启动")
            print()
        
        # 检查Python环境
        print("🐍 检查Python环境...")
        if sys.version_info < (3, 8):
            print("❌ Python版本过低，需要Python 3.8+")
            return False
        else:
            print("✅ Python环境正常")
        
        # 检查Node.js环境
        print("🟢 检查Node.js环境...")
        try:
            node_version = subprocess.run(
                ["node", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if node_version.returncode == 0:
                print(f"✅ Node.js环境正常: {node_version.stdout.strip()}")
                
                npm_version = subprocess.run(
                    ["npm", "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if npm_version.returncode == 0:
                    print(f"✅ npm版本: {npm_version.stdout.strip()}")
                else:
                    print("⚠️ npm未找到，但Node.js可用")
            else:
                print("❌ Node.js未找到")
                print("💡 需要安装Node.js 16+版本")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Node.js未找到")
            print("💡 需要安装Node.js 16+版本")
        
        # 检查RASA环境
        print("🤖 检查RASA环境...")
        try:
            rasa_version = subprocess.run(
                [sys.executable, "-m", "rasa", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=15
            )
            if rasa_version.returncode == 0:
                print(f"✅ RASA环境正常: {rasa_version.stdout.strip()}")
            else:
                print("❌ RASA未找到")
                print("💡 需要安装RASA: pip install rasa")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ RASA未找到")
            print("💡 需要安装RASA: pip install rasa")
        
        print()
        return True
    
    def check_files(self):
        """检查关键文件"""
        print("📋 检查关键文件...")
        
        required_files = [
            (self.base_dir / "backend" / "app.py", "后端应用文件"),
            (self.base_dir / "frontend" / "package.json", "前端配置文件"),
            (self.base_dir / "rasa" / "config.yml", "RASA配置文件"),
        ]
        
        all_exist = True
        for file_path, description in required_files:
            if file_path.exists():
                print(f"✅ {description}存在")
            else:
                print(f"❌ {description}不存在: {file_path}")
                all_exist = False
        
        print()
        return all_exist
    
    def stop_existing_services(self):
        """停止已存在的服务"""
        print("🛑 停止已存在的服务...")
        
        ports = [8001, 3000, 5005]
        for port in ports:
            if self.system == "Windows":
                try:
                    # Windows下查找并停止占用端口的进程
                    result = subprocess.run(
                        f'netstat -ano | findstr :{port}',
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    if result.stdout:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            if f':{port}' in line and 'LISTENING' in line:
                                parts = line.split()
                                if len(parts) >= 5:
                                    pid = parts[-1]
                                    subprocess.run(f'taskkill /F /PID {pid}', 
                                                 shell=True, capture_output=True)
                                    print(f"✅ 已停止端口 {port} 的进程 (PID: {pid})")
                except Exception as e:
                    print(f"⚠️ 停止端口 {port} 的服务时出错: {e}")
            else:
                # Unix/Linux下停止服务
                try:
                    subprocess.run(
                        f"lsof -ti:{port} | xargs kill -9",
                        shell=True,
                        capture_output=True,
                        timeout=5
                    )
                    print(f"✅ 已尝试停止端口 {port} 的服务")
                except subprocess.TimeoutExpired:
                    pass
                except Exception as e:
                    print(f"⚠️ 停止端口 {port} 的服务时出错: {e}")
        
        time.sleep(2)
        print()
    
    def create_service_commands(self):
        """创建各服务的启动命令"""
        commands = {}
        
        # 后端服务命令
        backend_dir = self.base_dir / "backend"
        commands['backend'] = {
            'title': 'Backend Service (8001)',
            'dir': str(backend_dir),
            'cmd': [
                sys.executable, '-m', 'uvicorn', 'app:app',
                '--host', '0.0.0.0',
                '--port', '8001',
                '--reload',
                '--reload-dir', '.',
                '--reload-exclude', '*.log',
                '--reload-exclude', '*.db',
                '--reload-exclude', '__pycache__',
                '--log-level', 'info',
                '--access-log',
                '--use-colors'
            ],
            'env': {
                'PYTHONPATH': str(backend_dir),
                'PYTHONIOENCODING': 'utf-8',
                'PYTHONUNBUFFERED': '1'
            }
        }
        
        # 前端服务命令
        frontend_dir = self.base_dir / "frontend"
        commands['frontend'] = {
            'title': 'Frontend Service (3000)',
            'dir': str(frontend_dir),
            'cmd': ['npm', 'run', 'start:v2'],
            'env': {
                'NODE_ENV': 'development',
                'BROWSER': 'none',
                'GENERATE_SOURCEMAP': 'true',
                'FAST_REFRESH': 'true',
                'WDS_SOCKET_HOST': 'localhost',
                'WDS_SOCKET_PORT': '3000',
                'WEBPACK_DEV_SERVER_LOG_LEVEL': 'verbose'
            }
        }
        
        # RASA服务命令
        rasa_dir = self.base_dir / "rasa"
        commands['rasa'] = {
            'title': 'RASA Service (5005)',
            'dir': str(rasa_dir),
            'cmd': [
                sys.executable, '-m', 'rasa', 'run',
                '--enable-api',
                '--cors', '*',
                '--port', '5005',
                '--log-level', 'INFO',
                '--debug'
            ],
            'env': {
                'PYTHONPATH': str(rasa_dir),
                'PYTHONIOENCODING': 'utf-8',
                'PYTHONUNBUFFERED': '1'
            }
        }
        
        return commands
    
    def start_windows_terminal_tabs(self):
        """使用Windows Terminal启动标签页"""
        print("🚀 启动Windows Terminal标签页...")
        print()
        
        commands = self.create_service_commands()
        
        # 构建Windows Terminal命令
        wt_cmd = ["wt"]
        
        for i, (service, config) in enumerate(commands.items()):
            if i > 0:
                wt_cmd.append(";")
            
            wt_cmd.extend([
                "new-tab", "--title", config['title'],
                "cmd", "/k", 
                f'cd /d "{config["dir"]}" && {" ".join(config["cmd"])}'
            ])
        
        try:
            subprocess.Popen(wt_cmd)
            print("✅ Windows Terminal已启动，请查看各个标签页的日志输出")
            return True
        except Exception as e:
            print(f"❌ 启动Windows Terminal失败: {e}")
            return False
    
    def start_traditional_windows(self):
        """使用传统cmd窗口启动"""
        print("🔄 使用传统方式启动（3个独立cmd窗口）...")
        print()
        
        commands = self.create_service_commands()
        
        for service, config in commands.items():
            try:
                cmd = [
                    "start", config['title'],
                    "cmd", "/k",
                    f'cd /d "{config["dir"]}" && {" ".join(config["cmd"])}'
                ]
                subprocess.Popen(cmd, shell=True)
                print(f"✅ 已启动: {config['title']}")
                time.sleep(1)  # 避免同时启动造成冲突
            except Exception as e:
                print(f"❌ 启动失败 {config['title']}: {e}")
        
        print("\n✅ 已启动3个独立的cmd窗口")
        return True
    
    def start_unix_terminals(self):
        """Unix/Linux系统启动"""
        print("🐧 Unix/Linux系统启动...")
        print()
        
        # 检查可用的终端
        terminals = ["gnome-terminal", "konsole", "xterm", "x-terminal-emulator"]
        available_terminal = None
        
        for terminal in terminals:
            if shutil.which(terminal):
                available_terminal = terminal
                break
        
        if not available_terminal:
            print("❌ 未找到可用的终端模拟器")
            print("💡 请手动启动各服务或安装gnome-terminal")
            return False
        
        print(f"✅ 使用终端: {available_terminal}")
        
        commands = self.create_service_commands()
        
        for service, config in commands.items():
            work_dir = Path(config['dir'])
            if work_dir.exists():
                try:
                    # 准备环境变量
                    env = os.environ.copy()
                    env.update(config['env'])
                    
                    cmd_str = " ".join(config['cmd'])
                    
                    if available_terminal == "gnome-terminal":
                        subprocess.Popen([
                            "gnome-terminal",
                            "--title", config['title'],
                            "--working-directory", str(work_dir),
                            "--", "bash", "-c", f"{cmd_str}; exec bash"
                        ], env=env)
                    elif available_terminal == "konsole":
                        subprocess.Popen([
                            "konsole",
                            "--title", config['title'],
                            "--workdir", str(work_dir),
                            "-e", "bash", "-c", f"{cmd_str}; exec bash"
                        ], env=env)
                    else:
                        subprocess.Popen([
                            available_terminal,
                            "-title", config['title'],
                            "-e", "bash", "-c", f"cd {work_dir} && {cmd_str}; exec bash"
                        ], env=env)
                    
                    print(f"✅ 已启动: {config['title']}")
                    time.sleep(2)
                except Exception as e:
                    print(f"❌ 启动失败 {config['title']}: {e}")
            else:
                print(f"❌ 目录不存在: {config['dir']}")
        
        return True
    
    def start_direct_processes(self):
        """直接启动进程（后台运行）"""
        print("🔄 直接启动服务进程...")
        print()
        
        commands = self.create_service_commands()
        
        for service, config in commands.items():
            work_dir = Path(config['dir'])
            if work_dir.exists():
                try:
                    # 准备环境变量
                    env = os.environ.copy()
                    env.update(config['env'])
                    
                    # 启动进程
                    process = subprocess.Popen(
                        config['cmd'],
                        cwd=str(work_dir),
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    self.processes.append((service, process))
                    print(f"✅ 已启动: {config['title']} (PID: {process.pid})")
                    time.sleep(2)
                except Exception as e:
                    print(f"❌ 启动失败 {config['title']}: {e}")
            else:
                print(f"❌ 目录不存在: {config['dir']}")
        
        return len(self.processes) > 0
    
    def print_service_info(self):
        """打印服务信息"""
        print("\n" + "=" * 60)
        print("🎉 智能对话训练平台启动完成！")
        print("=" * 60)
        print("🌐 服务地址:")
        print("   - 前端界面: http://localhost:3000")
        print("   - 后端API:  http://localhost:8001")
        print("   - 后端文档: http://localhost:8001/docs")
        print("   - API健康检查: http://localhost:8001/api/health")
        print("   - RASA API: http://localhost:5005")
        print()
        print("🔥 v2.0.0 新特性:")
        print("   - 双屏Excel数据导入")
        print("   - 智能追问逻辑")
        print("   - 系统性能监控")
        print("   - 完整的版本管理")
        print()
        print("💡 提示:")
        print("   - 每个服务都在独立的标签页/窗口中运行")
        print("   - 可以分别查看各服务的详细日志")
        print("   - 关闭任意标签页/窗口即可停止对应服务")
        
        if self.system == "Windows":
            print("   - 或使用 Ctrl+C 停止此脚本")
        else:
            print("   - 或使用 Ctrl+C 停止此脚本")
        
        print("=" * 60)
        print()
    
    def cleanup(self):
        """清理所有进程"""
        if self.processes:
            print("\n🛑 正在停止所有服务...")
            for name, process in self.processes:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"✅ {name} 服务已停止")
                except subprocess.TimeoutExpired:
                    try:
                        process.kill()
                        print(f"🔥 强制停止 {name} 服务")
                    except:
                        print(f"⚠️  无法停止 {name} 服务")
                except:
                    print(f"⚠️  停止 {name} 服务时出错")
    
    def signal_handler(self, signum, frame):
        """处理信号"""
        print(f"\n收到信号 {signum}，正在停止服务...")
        self.cleanup()
        sys.exit(0)
    
    def start(self):
        """主启动流程"""
        try:
            # 注册信号处理器
            if hasattr(signal, 'SIGINT'):
                signal.signal(signal.SIGINT, self.signal_handler)
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, self.signal_handler)
            
            self.print_banner()
            
            # 环境检查
            if not self.check_environment():
                print("❌ 环境检查失败，请检查依赖")
                return False
            
            # 文件检查
            if not self.check_files():
                print("❌ 关键文件缺失，请检查项目完整性")
                return False
            
            # 停止现有服务
            self.stop_existing_services()
            
            # 根据系统选择启动方式
            success = False
            
            if self.system == "Windows":
                # Windows系统
                if shutil.which("wt"):
                    # 优先使用Windows Terminal
                    success = self.start_windows_terminal_tabs()
                    if not success:
                        # 降级到传统cmd
                        success = self.start_traditional_windows()
                else:
                    # 直接使用传统cmd
                    success = self.start_traditional_windows()
            else:
                # Unix/Linux系统
                success = self.start_unix_terminals()
                if not success:
                    # 降级到直接启动进程
                    success = self.start_direct_processes()
            
            if success:
                self.print_service_info()
                
                # 如果有直接启动的进程，保持脚本运行
                if self.processes:
                    try:
                        print("按 Ctrl+C 停止所有服务...")
                        while True:
                            time.sleep(1)
                            # 检查进程是否还在运行
                            running_processes = []
                            for name, process in self.processes:
                                if process.poll() is None:
                                    running_processes.append((name, process))
                            self.processes = running_processes
                            
                            if not self.processes:
                                print("所有服务已停止")
                                break
                    except KeyboardInterrupt:
                        print("\n\n👋 收到停止信号，正在停止所有服务...")
                        self.cleanup()
                else:
                    # 如果是启动独立窗口/标签页，等待用户中断
                    try:
                        print("按 Ctrl+C 退出此脚本...")
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        print("\n\n👋 脚本已退出，服务继续在后台运行")
                        print("💡 如需停止所有服务，请关闭对应的窗口或标签页")
            else:
                print("❌ 启动失败，请检查上述错误信息")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 启动过程中出错: {e}")
            return False
        finally:
            self.cleanup()

def main():
    """主函数"""
    starter = PlatformTabsStarter()
    success = starter.start()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 