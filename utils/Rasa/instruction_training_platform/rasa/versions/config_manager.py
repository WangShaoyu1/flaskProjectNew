#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rasa配置文件管理工具 - 解决工作目录与版本目录重叠问题
"""

import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.versions_dir = Path(__file__).parent
        self.work_files = {
            'config.yml': self.project_root / 'config.yml',
            'domain.yml': self.project_root / 'data' / 'domain.yml',
            'nlu.yml': self.project_root / 'data' / 'nlu.yml',
            'rules.yml': self.project_root / 'data' / 'rules.yml'
        }
    
    def get_file_hash(self, file_path):
        """计算文件哈希值"""
        if not file_path.exists():
            return None
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def compare_with_versions(self):
        """对比当前工作文件与版本"""
        print("=== 配置文件版本对比 ===")
        
        version_dirs = [d for d in self.versions_dir.iterdir() 
                       if d.is_dir() and d.name.endswith('_data_config')]
        version_dirs.sort()
        
        for file_name, work_file in self.work_files.items():
            print(f"\n📁 {file_name}:")
            if not work_file.exists():
                print(f"   ❌ 工作文件不存在")
                continue
            
            work_hash = self.get_file_hash(work_file)
            print(f"   🔧 工作文件哈希: {work_hash[:8]}...")
            
            matches = []
            for version_dir in version_dirs:
                version_file = version_dir / file_name
                if version_file.exists():
                    version_hash = self.get_file_hash(version_file)
                    if work_hash == version_hash:
                        matches.append(version_dir.name)
                        print(f"   ✅ 匹配: {version_dir.name}")
                    else:
                        print(f"   ❌ 不匹配: {version_dir.name}")
            
            if not matches:
                print(f"   🔍 不匹配任何版本，可能有新修改")
    
    def switch_to_version(self, version_name):
        """切换到指定版本"""
        version_dir = self.versions_dir / version_name
        if not version_dir.exists():
            print(f"❌ 版本不存在: {version_name}")
            return False
        
        print(f"=== 切换到版本: {version_name} ===")
        
        # 备份当前文件
        backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.project_root / f"backup_work_{backup_time}"
        backup_dir.mkdir(exist_ok=True)
        
        for file_name, work_file in self.work_files.items():
            if work_file.exists():
                backup_file = backup_dir / file_name
                backup_file.parent.mkdir(exist_ok=True)
                shutil.copy2(work_file, backup_file)
                print(f"📦 备份: {file_name}")
        
        # 复制版本文件到工作目录
        for file_name, work_file in self.work_files.items():
            version_file = version_dir / file_name
            if version_file.exists():
                work_file.parent.mkdir(exist_ok=True)
                shutil.copy2(version_file, work_file)
                print(f"✅ 切换: {file_name}")
        
        print(f"🎉 切换完成! 备份在: {backup_dir}")
        return True

def main():
    manager = ConfigManager()
    
    while True:
        print("\n=== Rasa配置管理工具 ===")
        print("1. 对比当前文件与版本")
        print("2. 切换到指定版本") 
        print("3. 退出")
        
        choice = input("\n选择 (1-3): ").strip()
        
        if choice == '1':
            manager.compare_with_versions()
        elif choice == '2':
            version_name = input("输入版本名: ").strip()
            if version_name:
                manager.switch_to_version(version_name)
        elif choice == '3':
            break

if __name__ == "__main__":
    main() 