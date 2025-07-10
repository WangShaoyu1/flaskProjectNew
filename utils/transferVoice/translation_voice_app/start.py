#!/usr/bin/env python3
"""
翻译语音合成应用启动脚本
"""

import os
import sys
import time
import subprocess
import platform
import json
from pathlib import Path


class AppLauncher:
    """应用启动器"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.backend_dir = self.script_dir / "h5_api_server"
        self.frontend_dir = self.script_dir / "react_app"
        self.system = platform.system()
        
        # 加载端口配置
        self.backend_port, self.frontend_port = self.load_port_config()
        
        # 进程管理
        self.backend_process = None
        self.frontend_process = None
    
    def load_port_config(self):
        """加载端口配置"""
        try:
            config_file = self.script_dir / "config" / "ports.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    backend_port = config.get('backend', {}).get('port', 5000)
                    frontend_port = config.get('frontend', {}).get('port', 8080)
                    return backend_port, frontend_port
        except Exception:
            pass
        return 5000, 8080
    
    def print_banner(self):
        """打印启动横幅"""
        print("=" * 50)
        print("🎯 翻译语音合成应用")
        print("=" * 50)
        print(f"后端端口: {self.backend_port} | 前端端口: {self.frontend_port}")
        print()
    
    def start_backend(self):
        """启动后端服务器"""
        print("📡 启动后端服务器...")
        
        app_file = self.backend_dir / "app.py"
        if not app_file.exists():
            print(f"❌ 后端应用文件不存在: {app_file}")
            return False
        
        try:
            if self.system == "Windows":
                self.backend_process = subprocess.Popen(
                    [sys.executable, "app.py"],
                    cwd=self.backend_dir,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                self.backend_process = subprocess.Popen(
                    [sys.executable, "app.py"],
                    cwd=self.backend_dir
                )
            
            print("✅ 后端服务器启动成功")
            return True
            
        except Exception as e:
            print(f"❌ 后端启动失败: {e}")
            return False
    
    def wait_for_backend(self, timeout=15):
        """等待后端服务器启动"""
        print("⏳ 等待后端服务器就绪...")
        
        import urllib.request
        import urllib.error
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with urllib.request.urlopen(f"http://localhost:{self.backend_port}/api/health", timeout=2) as response:
                    if response.status == 200:
                        print("✅ 后端服务器已就绪")
                        return True
            except (urllib.error.URLError, urllib.error.HTTPError):
                pass
            
            time.sleep(1)
            print(".", end="", flush=True)
        
        print("\n⚠️  后端服务器启动超时，继续启动前端")
        return False
    
    def start_frontend(self):
        """启动前端应用"""
        print("🌐 启动前端应用...")
        
        package_file = self.frontend_dir / "package.json"
        if not package_file.exists():
            print(f"❌ package.json不存在: {package_file}")
            return False
        
        try:
            # 设置环境变量
            env = os.environ.copy()
            env['PORT'] = str(self.frontend_port)
            env['BROWSER'] = 'none'
            env['GENERATE_SOURCEMAP'] = 'false'
            env['DISABLE_ESLINT_PLUGIN'] = 'true'
            
            # 启动React应用
            self.frontend_process = subprocess.Popen(
                ["npm", "start"],
                cwd=self.frontend_dir,
                shell=True,
                env=env
            )
            
            print("✅ 前端应用启动成功")
            return True
            
        except Exception as e:
            print(f"❌ 前端启动失败: {e}")
            return False
    
    def cleanup(self):
        """清理进程"""
        print("\n🛑 正在关闭应用...")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                print("✅ 前端应用已关闭")
            except:
                self.frontend_process.kill()
                print("⚠️  强制关闭前端应用")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("✅ 后端服务器已关闭")
            except:
                self.backend_process.kill()
                print("⚠️  强制关闭后端服务器")
    
    def run(self):
        """运行应用"""
        try:
            self.print_banner()
            
            # 启动后端
            if not self.start_backend():
                return False
            
            # 等待后端启动
            self.wait_for_backend()
            
            print()
            
            # 启动前端
            if not self.start_frontend():
                return False
            
            print()
            print("🎉 应用启动完成！")
            print("📖 访问地址:")
            print(f"   - 后端API: http://localhost:{self.backend_port}")
            print(f"   - 前端应用: http://localhost:{self.frontend_port}")
            print("   - 按 Ctrl+C 停止应用")
            print()
            
            # 等待用户中断
            try:
                if self.frontend_process:
                    self.frontend_process.wait()
                elif self.backend_process:
                    self.backend_process.wait()
                else:
                    input("按回车键退出...")
            except KeyboardInterrupt:
                pass
            
            return True
            
        except KeyboardInterrupt:
            print("\n⚠️  用户中断")
            return True
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False
        finally:
            self.cleanup()


def main():
    """主函数"""
    launcher = AppLauncher()
    success = launcher.run()
    
    if success:
        print("👋 再见！")
    else:
        print("❌ 启动失败")
        sys.exit(1)


if __name__ == "__main__":
    main() 