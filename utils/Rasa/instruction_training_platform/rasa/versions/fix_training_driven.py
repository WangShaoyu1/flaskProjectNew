#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正版本管理为训练驱动模式
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def analyze_current_situation():
    """分析当前情况"""
    print("=== 分析当前版本管理状况 ===")
    
    project_root = Path(__file__).parent.parent
    versions_dir = Path(__file__).parent
    models_dir = project_root / 'models'
    
    # 获取模型信息
    models = []
    if models_dir.exists():
        for model_file in models_dir.glob("*.tar.gz"):
            name = model_file.stem
            if len(name) >= 15:
                time_part = name[:15]  # 20250621-002404
                try:
                    model_time = datetime.strptime(time_part, "%Y%m%d-%H%M%S")
                    expected_version = model_time.strftime("%Y%m%d%H%M_data_config")
                    models.append({
                        'file': model_file.name,
                        'time': model_time,
                        'expected_version': expected_version
                    })
                except:
                    pass
    
    # 获取版本信息
    versions = []
    for version_dir in versions_dir.glob("*_data_config"):
        if version_dir.is_dir():
            versions.append(version_dir.name)
    
    print(f"\n📊 当前状况:")
    print(f"模型数量: {len(models)}")
    for model in models:
        print(f"  - {model['file']} → 应对应版本: {model['expected_version']}")
    
    print(f"\n版本数量: {len(versions)}")
    for version in sorted(versions):
        print(f"  - {version}")
    
    # 分析问题
    expected_versions = {model['expected_version'] for model in models}
    current_versions = set(versions)
    
    extra_versions = current_versions - expected_versions
    missing_versions = expected_versions - current_versions
    
    print(f"\n🔍 问题分析:")
    if extra_versions:
        print(f"多余版本: {extra_versions}")
    if missing_versions:
        print(f"缺失版本: {missing_versions}")
    
    if not extra_versions and not missing_versions:
        print("✅ 版本与模型一致")
        return True
    else:
        print("❌ 版本与模型不一致")
        return False

def fix_to_training_driven():
    """修正为训练驱动模式"""
    print("\n=== 修正为训练驱动模式 ===")
    
    project_root = Path(__file__).parent.parent
    versions_dir = Path(__file__).parent
    models_dir = project_root / 'models'
    data_dir = project_root / 'data'
    
    # 1. 分析应该保留的版本
    models = []
    if models_dir.exists():
        for model_file in models_dir.glob("*.tar.gz"):
            name = model_file.stem
            if len(name) >= 15:
                time_part = name[:15]
                try:
                    model_time = datetime.strptime(time_part, "%Y%m%d-%H%M%S")
                    expected_version = model_time.strftime("%Y%m%d%H%M_data_config")
                    models.append({
                        'file': model_file.name,
                        'time': model_time,
                        'expected_version': expected_version
                    })
                except:
                    pass
    
    expected_versions = {model['expected_version'] for model in models}
    
    # 2. 清理多余版本
    print(f"\n🗑️  清理多余版本:")
    for version_dir in versions_dir.glob("*_data_config"):
        if version_dir.is_dir() and version_dir.name not in expected_versions:
            backup_name = f"backup_{version_dir.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = versions_dir / backup_name
            shutil.move(version_dir, backup_path)
            print(f"   ✅ 移除: {version_dir.name} → {backup_name}")
    
    # 3. 确保data文件夹是工作区
    print(f"\n📁 确保data文件夹为工作区:")
    
    # 删除版本标记文件（恢复data为工作区）
    version_marker = project_root / '.current_version'
    if version_marker.exists():
        version_marker.unlink()
        print(f"   ✅ 删除版本标记文件")
    
    # 确保data文件夹是最新工作内容
    print(f"   ✅ data文件夹保持为工作区")
    
    # 4. 验证必要版本存在
    missing_versions = expected_versions - {d.name for d in versions_dir.glob("*_data_config") if d.is_dir()}
    
    if missing_versions:
        print(f"\n⚠️  缺失版本: {missing_versions}")
        print("这些版本将在下次对应模型重新训练时自动创建")
    
    print(f"\n✅ 修正完成!")
    print(f"📋 新的工作模式:")
    print(f"  - data文件夹: 工作区（可随时修改）")
    print(f"  - versions文件夹: 训练时的配置快照")
    print(f"  - 训练成功后: 自动创建版本快照")
    print(f"  - 版本数量 = 模型数量: {len(expected_versions)}")

def show_correct_workflow():
    """显示正确的工作流程"""
    print("\n" + "="*60)
    print("🎯 训练驱动的正确工作流程")
    print("="*60)
    
    print(f"\n📝 日常开发:")
    print(f"1. 直接编辑 rasa/data/ 下的yml文件")
    print(f"2. 直接编辑 rasa/config.yml")
    print(f"3. 随时修改，无需手动创建版本")
    
    print(f"\n🚀 训练流程:")
    print(f"1. 修改配置文件（在data文件夹中）")
    print(f"2. 开始训练模型")
    print(f"3. 训练成功 → 自动创建版本快照")
    print(f"4. 版本记录训练时使用的配置")
    
    print(f"\n📊 管理原则:")
    print(f"- data文件夹 = 最新工作内容")
    print(f"- versions文件夹 = 历史训练快照")
    print(f"- 版本数量 = 模型数量")
    print(f"- 无需手动创建版本")

if __name__ == "__main__":
    print("训练驱动版本管理修正工具")
    print("=" * 50)
    
    # 分析当前状况
    is_consistent = analyze_current_situation()
    
    if not is_consistent:
        confirm = input(f"\n是否修正为训练驱动模式? (y/n): ").lower().strip()
        if confirm in ['y', 'yes', '是']:
            fix_to_training_driven()
            show_correct_workflow()
        else:
            print("取消修正")
    else:
        print("✅ 当前已符合训练驱动模式")
        show_correct_workflow() 