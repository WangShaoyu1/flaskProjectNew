#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
清除历史训练数据脚本
包括：
1. 内存中的训练记录
2. RASA模型文件
3. 训练日志
4. 临时文件
"""

import os
import shutil
import glob
from pathlib import Path
import requests
import json

def print_section(title):
    """打印分节标题"""
    print("\n" + "="*50)
    print(f"🧹 {title}")
    print("="*50)

def clear_rasa_models():
    """清除RASA模型文件"""
    print_section("清除RASA模型文件")
    
    models_dir = Path("rasa/models")
    if models_dir.exists():
        model_files = list(models_dir.glob("*.tar.gz"))
        if model_files:
            print(f"找到 {len(model_files)} 个模型文件:")
            for model_file in model_files:
                print(f"  - {model_file.name}")
                try:
                    model_file.unlink()
                    print(f"    ✅ 已删除")
                except Exception as e:
                    print(f"    ❌ 删除失败: {e}")
        else:
            print("没有找到模型文件")
    else:
        print("模型目录不存在")

def clear_training_logs():
    """清除训练日志"""
    print_section("清除训练日志")
    
    log_files = [
        "backend/logs/training.log",
        "backend/logs/api_requests.log",
        "backend/logs/system.log",
        "backend/logs/errors.log",
        "backend/logs/database.log"
    ]
    
    for log_file in log_files:
        log_path = Path(log_file)
        if log_path.exists():
            try:
                # 清空文件内容而不是删除文件
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write("")
                print(f"✅ 已清空: {log_file}")
            except Exception as e:
                print(f"❌ 清空失败: {log_file} - {e}")
        else:
            print(f"⏭️  文件不存在: {log_file}")

def clear_rasa_training_data():
    """清除RASA训练数据目录"""
    print_section("清除RASA训练数据")
    
    # 清除backend/rasa_data目录（如果存在）
    rasa_data_dir = Path("backend/rasa_data")
    if rasa_data_dir.exists():
        try:
            shutil.rmtree(rasa_data_dir)
            print(f"✅ 已删除目录: {rasa_data_dir}")
        except Exception as e:
            print(f"❌ 删除失败: {rasa_data_dir} - {e}")
    
    # 清除rasa/data目录中的训练文件
    rasa_work_dir = Path("rasa/data")
    if rasa_work_dir.exists():
        training_files = ["nlu.yml", "domain.yml", "stories.yml", "rules.yml"]
        for file_name in training_files:
            file_path = rasa_work_dir / file_name
            if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"✅ 已删除: {file_path}")
                except Exception as e:
                    print(f"❌ 删除失败: {file_path} - {e}")

def clear_memory_training_records():
    """清除内存中的训练记录"""
    print_section("清除内存训练记录")
    
    try:
        # 尝试连接API清除内存数据
        response = requests.post("http://localhost:8001/api/v2/training/clear-all", timeout=5)
        if response.status_code == 200:
            print("✅ 内存训练记录已清除")
        else:
            print(f"⚠️  API清除失败: {response.status_code}")
    except Exception as e:
        print(f"⚠️  API连接失败: {e}")
        print("💡 需要手动重启后端服务来清除内存数据")

def clear_temp_files():
    """清除临时文件"""
    print_section("清除临时文件")
    
    temp_patterns = [
        "*.tmp",
        "*.temp",
        "*~",
        "*.bak",
        "*.log.*",
        "__pycache__",
        "*.pyc"
    ]
    
    for pattern in temp_patterns:
        files = glob.glob(pattern, recursive=True)
        for file_path in files:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"✅ 已删除文件: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"✅ 已删除目录: {file_path}")
            except Exception as e:
                print(f"❌ 删除失败: {file_path} - {e}")

def main():
    """主函数"""
    print("🧹 开始清除历史训练数据...")
    
    # 确认操作
    confirm = input("\n⚠️  这将清除所有历史训练数据，包括模型文件和日志。确认继续吗？(y/N): ")
    if confirm.lower() != 'y':
        print("❌ 操作已取消")
        return
    
    # 执行清除操作
    clear_rasa_models()
    clear_training_logs()
    clear_rasa_training_data()
    clear_memory_training_records()
    clear_temp_files()
    
    print_section("清除完成")
    print("✅ 历史训练数据清除完成！")
    print("💡 建议重启后端服务以确保内存数据完全清除")
    print("💡 重启命令: cd backend && python app.py")

if __name__ == "__main__":
    main() 