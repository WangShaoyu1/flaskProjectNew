import os
import subprocess
import hashlib
from flask import Blueprint, render_template, redirect, url_for, request, jsonify

webHooks = Blueprint('webHooks', __name__)


# 动态获取Git仓库URL
def get_git_repo_url():
    config_path = os.path.join(BASE_PATH, '.git', 'config')
    if not os.path.exists(config_path):
        raise FileNotFoundError(f".git/config 文件不存在于 {BASE_PATH}")

    with open(config_path, 'r') as file:
        for line in file:
            if 'url = ' in line:
                return line.strip().split(' = ')[1]
    raise ValueError("远程仓库URL未能从.config文件中解析")


def get_file_hash(file_path):
    """获取文件的hash值"""
    if not os.path.isfile(file_path):
        return None
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def install_nvm_and_node():
    try:
        # 下载并安装 NVM
        if os.name == 'nt':
            raise RuntimeError("请手动安装NVM并配置环境变量。")
        else:
            install_nvm_command = 'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash'
            subprocess.run(install_nvm_command, shell=True, executable='/bin/bash', check=True)

        # 重新加载 shell 配置以确保 NVM 可用
        load_nvm_command = 'export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"'
        subprocess.run(load_nvm_command, shell=True, executable='/bin/bash', check=True)

        # 安装最新的 Node.js 版本
        install_node_command = 'nvm install node'
        subprocess.run(f'{load_nvm_command} && {install_node_command}', shell=True, executable='/bin/bash', check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("NVM 或 Node.js 安装失败") from e


# 获取 npm 全局模块安装路径
def get_pm2_path():
    try:
        # 手动加载 NVM 环境并获取当前使用的 Node 版本
        load_nvm_command = 'export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"'
        nvm_current_command = 'nvm current'
        command = f'{load_nvm_command} && {nvm_current_command}'
        nvm_current_process = subprocess.run(command, capture_output=True, text=True, shell=True,
                                             executable='/bin/bash', check=True)
        current_node_version = nvm_current_process.stdout.strip()
        print(f"当前使用的 Node 版本是，为什么不打印出来: {current_node_version}")
        if current_node_version == 'none':
            print("当前没有 Node 版本，将安装 NVM 及最新版本的 Node.js")
            install_nvm_and_node()
            # 重新加载 NVM 环境并获取当前使用的 Node 版本
            nvm_current_process = subprocess.run(command, capture_output=True, text=True, shell=True,
                                                 executable='/bin/bash', check=True)
            current_node_version = nvm_current_process.stdout.strip()

        # 获取 NVM 安装目录
        nvm_dir = os.environ.get('NVM_HOME') or os.environ.get('NVM_DIR')
        print(f"NVM 安装目录: {nvm_dir}")
        if not nvm_dir:
            raise RuntimeError("NVM 目录未找到。这可能是因为 NVM 没有正确安装或环境变量未设置")

        # 构建 npm 全局路径
        npm_global_root = os.path.join(nvm_dir, 'versions', 'node', f'{current_node_version}', 'lib', 'node_modules')
        if not os.path.exists(npm_global_root):
            # 如果路径不存在，切换到没有 'versions' 和 'node' 级别的路径
            npm_global_root = os.path.join(nvm_dir, current_node_version)
        print(f"npm 全局模块安装路径: {npm_global_root}")
        # 构建 pm2 可执行文件路径
        if os.name == 'nt':
            pm2_path = os.path.join(npm_global_root, 'pm2.cmd')
        else:
            pm2_path = os.path.join(npm_global_root, 'pm2', 'bin', 'pm2')
        print(f"pm2 可执行文件路径: {pm2_path}")
        # 检查可执行文件是否存在
        if not os.path.exists(pm2_path):
            raise FileNotFoundError(f"pm2 不在全局路径 {npm_global_root} 中找到")

        return pm2_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError("无法获取当前 Node 版本") from e


# 基础路径配置为上一级目录（项目的根目录）
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIT_REPO_URL = get_git_repo_url()
PROJECT_NAME = GIT_REPO_URL.split('/')[-1].replace('.git', '')


@webHooks.route('/api/webHooks', methods=['POST'])
def get_webHooks():
    data = request.json
    print(f"BASE_PATH: {BASE_PATH}")
    print(f"GIT_REPO_URL: {GIT_REPO_URL}")
    print(f"PROJECT_NAME: {PROJECT_NAME}")
    print(f"data: {data}")
    print(f"收到来自 {data.get('repository', {}).get('name')} 的推送事件")
    # 检查是否是push事件并且目标分支是master
    if data.get('ref') == 'refs/heads/master':
        # 确保目录在pull之前是存在的
        if not os.path.exists(BASE_PATH):
            os.makedirs(BASE_PATH)

        # 切换到代码目录并拉取最新代码
        subprocess.call(['git', 'checkout', 'master'], cwd=BASE_PATH)
        subprocess.call(['git', 'pull', 'origin', 'master'], cwd=BASE_PATH)

        # 获取上一次的requirements.txt hash值
        requirements_path = os.path.join(BASE_PATH, 'requirements.txt')
        last_requirements_hash = get_file_hash(requirements_path)

        # 获取最新的requirements.txt hash值
        new_requirements_hash = get_file_hash(requirements_path)

        if last_requirements_hash != new_requirements_hash:
            # 如果 requirements.txt 有变化，执行 pip install -r requirements.txt
            subprocess.call(['pip', 'install', '-r', 'requirements.txt'], cwd=BASE_PATH)

        pm2_path = get_pm2_path()

        subprocess.call([pm2_path, 'restart', PROJECT_NAME])
    return jsonify({'status': 'success'}), 200
