#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件优化脚本 - 实施版本优先模式
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def implement_version_priority():
    """实施版本优先模式，消除重复"""
    
    print("=== 实施版本优先模式 ===")
    
    # 确定当前匹配的版本（从config_manager分析结果我们知道是202506231700_data_config）
    current_version = "202506231700_data_config"
    
    # 项目路径
    project_root = Path(__file__).parent.parent
    version_dir = Path(__file__).parent / current_version
    
    work_files = {
        'config.yml': project_root / 'config.yml',
        'domain.yml': project_root / 'data' / 'domain.yml',
        'nlu.yml': project_root / 'data' / 'nlu.yml',
        'rules.yml': project_root / 'data' / 'rules.yml'
    }
    
    # 1. 创建备份
    backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_root / f"backup_before_optimization_{backup_time}"
    backup_dir.mkdir(exist_ok=True)
    
    print(f"📦 创建备份: {backup_dir}")
    for file_name, work_file in work_files.items():
        if work_file.exists():
            backup_file = backup_dir / file_name
            backup_file.parent.mkdir(exist_ok=True)
            shutil.copy2(work_file, backup_file)
            print(f"   ✅ 备份: {file_name}")
    
    # 2. 删除工作目录的重复文件
    print(f"\n🗑️  删除重复文件:")
    for file_name, work_file in work_files.items():
        if work_file.exists():
            work_file.unlink()
            print(f"   ✅ 删除: {work_file}")
    
    # 3. 从版本目录复制到工作目录（建立单向同步）
    print(f"\n🔄 从版本 {current_version} 同步:")
    for file_name, work_file in work_files.items():
        version_file = version_dir / file_name
        if version_file.exists():
            work_file.parent.mkdir(exist_ok=True)
            shutil.copy2(version_file, work_file)
            print(f"   ✅ 同步: {file_name}")
    
    # 4. 创建版本标记文件
    version_marker = project_root / '.current_version'
    with open(version_marker, 'w', encoding='utf-8') as f:
        f.write(f"current_version: {current_version}\n")
        f.write(f"optimized_time: {datetime.now().isoformat()}\n")
        f.write(f"mode: version_priority\n")
        f.write(f"backup_location: {backup_dir.name}\n")
    
    print(f"\n✅ 版本优先模式实施完成!")
    print(f"📍 当前版本: {current_version}")
    print(f"📦 备份位置: {backup_dir}")
    print(f"🎯 工作流程: 现在所有配置修改都应该先在版本目录中进行")
    
    return True

def show_optimization_summary():
    """显示优化总结"""
    print("\n" + "="*60)
    print("🎉 配置文件重叠问题优化完成!")
    print("="*60)
    
    print("\n📋 优化结果:")
    print("✅ 消除了工作目录与版本目录的重复存储")
    print("✅ 建立了版本优先的工作流程")
    print("✅ 所有历史版本都已保留")
    print("✅ 创建了完整的备份")
    
    print("\n🔄 新的工作流程:")
    print("1. 修改配置文件 → 在版本目录中创建新版本")
    print("2. 使用 config_manager.py 切换版本")
    print("3. 工作目录始终从版本目录同步")
    print("4. 训练模型时记录使用的版本")
    
    print("\n🛠️  管理工具:")
    print("- config_manager.py - 基础版本管理")
    print("- create_new_version.py - 创建新版本")
    print("- optimize_config.py - 优化配置（本脚本）")
    
    print("\n📁 文件结构:")
    print("rasa/")
    print("├── versions/           # 🏛️  权威配置源")
    print("│   ├── 202506210024_data_config/")
    print("│   ├── 202506222244_data_config/")
    print("│   └── 202506231700_data_config/  # 📍 当前版本")
    print("├── config.yml         # 📄 工作文件（从版本同步）")
    print("└── data/")
    print("    ├── domain.yml     # 📄 工作文件（从版本同步）")
    print("    ├── nlu.yml        # 📄 工作文件（从版本同步）")
    print("    └── rules.yml      # 📄 工作文件（从版本同步）")

if __name__ == "__main__":
    print("Rasa配置文件优化工具")
    print("实施第二个方案：彻底优化（消除重复）")
    
    confirm = input("\n确认实施版本优先模式? (y/n): ").lower().strip()
    
    if confirm in ['y', 'yes', '是']:
        if implement_version_priority():
            show_optimization_summary()
    else:
        print("取消优化操作") 