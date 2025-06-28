#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级Rasa配置文件管理工具 - 支持彻底优化方案
实现版本优先的工作流程，消除重叠问题
"""

import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

class AdvancedConfigManager:
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
    
    def get_version_dirs(self):
        """获取所有版本目录"""
        version_dirs = [d for d in self.versions_dir.iterdir() 
                       if d.is_dir() and d.name.endswith('_data_config')]
        return sorted(version_dirs)
    
    def find_matching_version(self):
        """找到与当前工作文件完全匹配的版本"""
        version_dirs = self.get_version_dirs()
        
        for version_dir in version_dirs:
            matches = 0
            total = 0
            
            for file_name, work_file in self.work_files.items():
                if work_file.exists():
                    total += 1
                    version_file = version_dir / file_name
                    if (version_file.exists() and 
                        self.get_file_hash(work_file) == self.get_file_hash(version_file)):
                        matches += 1
            
            if matches == total and total > 0:
                return version_dir.name
        
        return None
    
    def analyze_redundancy(self):
        """分析重复文件问题"""
        print("=== 配置文件重复分析 ===")
        
        matching_version = self.find_matching_version()
        
        if matching_version:
            print(f"✅ 当前工作文件完全匹配版本: {matching_version}")
            print("\n🔄 检测到重复存储问题:")
            
            for file_name, work_file in self.work_files.items():
                if work_file.exists():
                    version_file = self.versions_dir / matching_version / file_name
                    if version_file.exists():
                        work_size = work_file.stat().st_size
                        print(f"   - {file_name}: {work_size:,} 字节 (重复)")
            
            print(f"\n💡 建议: 可以实施版本优先模式")
            return matching_version
        else:
            print("❌ 当前工作文件不完全匹配任何版本")
            print("需要先创建版本或切换到现有版本")
            return None
    
    def implement_version_priority_mode(self, version_name):
        """实施版本优先模式"""
        version_dir = self.versions_dir / version_name
        
        if not version_dir.exists():
            print(f"❌ 版本不存在: {version_name}")
            return False
        
        print(f"=== 实施版本优先模式: {version_name} ===")
        
        # 1. 备份当前工作文件
        backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.project_root / f"backup_before_optimization_{backup_time}"
        backup_dir.mkdir(exist_ok=True)
        
        print(f"📦 备份当前工作文件到: {backup_dir}")
        for file_name, work_file in self.work_files.items():
            if work_file.exists():
                backup_file = backup_dir / file_name
                backup_file.parent.mkdir(exist_ok=True)
                shutil.copy2(work_file, backup_file)
                print(f"   ✅ 备份: {file_name}")
        
        # 2. 删除工作目录的配置文件
        print(f"\n🗑️  删除工作目录中的重复文件:")
        for file_name, work_file in self.work_files.items():
            if work_file.exists():
                work_file.unlink()
                print(f"   ✅ 删除: {work_file}")
        
        # 3. 创建从版本到工作目录的符号链接或复制
        print(f"\n🔗 建立版本优先链接:")
        for file_name, work_file in self.work_files.items():
            version_file = version_dir / file_name
            if version_file.exists():
                work_file.parent.mkdir(exist_ok=True)
                
                # 在Windows上创建硬链接或复制文件
                try:
                    # 尝试创建硬链接
                    os.link(str(version_file), str(work_file))
                    print(f"   🔗 硬链接: {file_name}")
                except:
                    # 如果硬链接失败，则复制文件
                    shutil.copy2(version_file, work_file)
                    print(f"   📄 复制: {file_name}")
        
        # 4. 创建版本优先标识文件
        version_marker = self.project_root / '.current_version'
        with open(version_marker, 'w', encoding='utf-8') as f:
            f.write(f"{version_name}\n")
            f.write(f"created: {datetime.now().isoformat()}\n")
            f.write("mode: version_priority\n")
        
        print(f"✅ 版本优先模式实施完成!")
        print(f"📝 当前版本标记: {version_name}")
        print(f"📦 备份位置: {backup_dir}")
        
        return True
    
    def check_version_consistency(self):
        """检查版本一致性"""
        print("=== 版本一致性检查 ===")
        
        version_marker = self.project_root / '.current_version'
        if version_marker.exists():
            with open(version_marker, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                current_version = lines[0].strip()
                print(f"📍 标记的当前版本: {current_version}")
        else:
            print("⚠️  没有版本标记文件")
            current_version = None
        
        # 检查工作文件与哪个版本匹配
        matching_version = self.find_matching_version()
        
        if current_version and matching_version:
            if current_version == matching_version:
                print(f"✅ 版本一致: {current_version}")
                return True
            else:
                print(f"❌ 版本不一致!")
                print(f"   标记版本: {current_version}")
                print(f"   实际匹配: {matching_version}")
                return False
        else:
            print("⚠️  无法确定版本一致性")
            return False
    
    def list_versions_with_status(self):
        """列出版本及其状态"""
        print("=== 版本状态列表 ===")
        
        version_dirs = self.get_version_dirs()
        matching_version = self.find_matching_version()
        
        for i, version_dir in enumerate(version_dirs, 1):
            version_name = version_dir.name
            print(f"\n{i}. {version_name}")
            
            # 检查文件完整性
            missing_files = []
            for file_name in self.work_files.keys():
                if not (version_dir / file_name).exists():
                    missing_files.append(file_name)
            
            if missing_files:
                print(f"   ⚠️  缺少文件: {', '.join(missing_files)}")
            else:
                print(f"   ✅ 文件完整")
            
            # 检查是否与当前工作文件匹配
            if version_name == matching_version:
                print(f"   🎯 当前匹配版本")
            
            # 检查创建时间
            try:
                create_time = datetime.fromtimestamp(version_dir.stat().st_ctime)
                print(f"   📅 创建时间: {create_time.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                pass

def main():
    print("高级Rasa配置文件管理工具")
    print("=" * 50)
    
    manager = AdvancedConfigManager()
    
    while True:
        print("\n=== 高级配置管理选项 ===")
        print("1. 分析重复问题")
        print("2. 实施版本优先模式")
        print("3. 检查版本一致性")
        print("4. 版本状态列表")
        print("5. 基础版本管理")
        print("6. 退出")
        
        choice = input("\n选择 (1-6): ").strip()
        
        if choice == '1':
            matching_version = manager.analyze_redundancy()
            if matching_version:
                implement = input(f"\n是否立即实施版本优先模式? (y/n): ").lower().strip()
                if implement in ['y', 'yes', '是']:
                    manager.implement_version_priority_mode(matching_version)
        
        elif choice == '2':
            manager.list_versions_with_status()
            version_name = input("\n输入要实施的版本名: ").strip()
            if version_name:
                manager.implement_version_priority_mode(version_name)
        
        elif choice == '3':
            manager.check_version_consistency()
        
        elif choice == '4':
            manager.list_versions_with_status()
        
        elif choice == '5':
            # 调用基础配置管理器
            os.system("python config_manager.py")
        
        elif choice == '6':
            break
        
        else:
            print("无效选择")

if __name__ == "__main__":
    main() 