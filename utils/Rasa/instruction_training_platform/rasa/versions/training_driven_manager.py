#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
训练驱动的版本管理系统
- data文件夹是工作区（最新内容）
- 训练成功后自动创建版本快照
- 版本数量与模型数量一致
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

class TrainingDrivenManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.versions_dir = Path(__file__).parent
        self.data_dir = self.project_root / 'data'
        self.models_dir = self.project_root / 'models'
        
        self.config_files = [
            'config.yml',      # 在rasa根目录
            'domain.yml',      # 在data目录
            'nlu.yml',         # 在data目录  
            'rules.yml'        # 在data目录
        ]
    
    def get_models_info(self):
        """获取现有模型信息"""
        if not self.models_dir.exists():
            return []
        
        models = []
        for model_file in self.models_dir.glob("*.tar.gz"):
            # 从文件名提取时间戳
            name = model_file.stem
            if len(name) >= 15:  # 20250621-002404-xxx格式
                time_part = name[:15]  # 20250621-002404
                try:
                    model_time = datetime.strptime(time_part, "%Y%m%d-%H%M%S")
                    models.append({
                        'file': model_file.name,
                        'path': model_file,
                        'time': model_time,
                        'version_name': model_time.strftime("%Y%m%d%H%M_data_config")
                    })
                except:
                    pass
        
        return sorted(models, key=lambda x: x['time'])
    
    def get_existing_versions(self):
        """获取现有版本信息"""
        versions = []
        for version_dir in self.versions_dir.glob("*_data_config"):
            if version_dir.is_dir():
                versions.append(version_dir.name)
        return sorted(versions)
    
    def analyze_version_model_consistency(self):
        """分析版本与模型的一致性"""
        print("=== 训练驱动版本管理分析 ===")
        
        models = self.get_models_info()
        versions = self.get_existing_versions()
        
        print(f"\n📊 当前状况:")
        print(f"   模型数量: {len(models)}")
        print(f"   版本数量: {len(versions)}")
        
        print(f"\n🤖 模型列表:")
        for i, model in enumerate(models, 1):
            print(f"   {i}. {model['file']}")
            print(f"      时间: {model['time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      对应版本: {model['version_name']}")
        
        print(f"\n📁 版本列表:")
        for i, version in enumerate(versions, 1):
            print(f"   {i}. {version}")
        
        # 检查一致性
        expected_versions = [model['version_name'] for model in models]
        
        print(f"\n🔍 一致性分析:")
        if len(models) == len(versions) and set(expected_versions) == set(versions):
            print("   ✅ 版本与模型完全一致")
            return True, models, versions
        else:
            print("   ❌ 版本与模型不一致")
            
            missing_versions = set(expected_versions) - set(versions)
            extra_versions = set(versions) - set(expected_versions)
            
            if missing_versions:
                print(f"   🔍 缺少版本: {missing_versions}")
            if extra_versions:
                print(f"   🗑️  多余版本: {extra_versions}")
            
            return False, models, versions
    
    def cleanup_extra_versions(self, models, versions):
        """清理多余的版本"""
        expected_versions = [model['version_name'] for model in models]
        extra_versions = set(versions) - set(expected_versions)
        
        if not extra_versions:
            print("✅ 没有多余版本需要清理")
            return
        
        print(f"\n🗑️  清理多余版本:")
        for version in extra_versions:
            version_path = self.versions_dir / version
            if version_path.exists():
                # 备份后删除
                backup_name = f"backup_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_path = self.versions_dir / backup_name
                shutil.move(version_path, backup_path)
                print(f"   ✅ 移除: {version} → {backup_name}")
    
    def create_missing_versions(self, models, versions):
        """为现有模型创建缺失的版本"""
        expected_versions = [model['version_name'] for model in models]
        missing_versions = set(expected_versions) - set(versions)
        
        if not missing_versions:
            print("✅ 所有模型都有对应版本")
            return
        
        print(f"\n📝 为现有模型创建缺失版本:")
        
        # 需要用户确认从哪里获取配置
        print("⚠️  需要为以下模型补充版本配置:")
        for model in models:
            if model['version_name'] in missing_versions:
                print(f"   - {model['file']} → {model['version_name']}")
        
        response = input("\n选择配置来源:\n1. 从当前data文件夹\n2. 从最近的版本\n3. 手动指定\n请选择 (1-3): ")
        
        if response == '1':
            self._create_versions_from_current_data(models, missing_versions)
        elif response == '2':
            self._create_versions_from_latest(models, missing_versions)
        else:
            print("请手动创建版本")
    
    def _create_versions_from_current_data(self, models, missing_versions):
        """从当前data文件夹创建版本"""
        print("📄 从当前data文件夹创建版本...")
        
        for model in models:
            if model['version_name'] in missing_versions:
                version_dir = self.versions_dir / model['version_name']
                version_dir.mkdir(exist_ok=True)
                
                # 复制配置文件
                for config_file in self.config_files:
                    if config_file == 'config.yml':
                        src = self.project_root / config_file
                    else:
                        src = self.data_dir / config_file
                    
                    if src.exists():
                        dst = version_dir / config_file
                        shutil.copy2(src, dst)
                        print(f"   ✅ 复制: {config_file}")
                
                # 创建版本信息
                self._create_version_info(version_dir, model, "从当前data文件夹重建")
                print(f"   📝 创建版本: {model['version_name']}")
    
    def _create_version_info(self, version_dir, model, source):
        """创建版本信息文件"""
        info_file = version_dir / 'version_info.md'
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"""# 版本信息 - {model['version_name']}

## 对应模型
- 文件名: {model['file']}
- 训练时间: {model['time'].strftime('%Y-%m-%d %H:%M:%S')}

## 创建方式
{source}

## 版本说明
这是训练模型 {model['file']} 时使用的配置快照。

## 配置文件
- config.yml - Rasa配置
- domain.yml - 领域定义  
- nlu.yml - 训练数据
- rules.yml - 规则定义

## 备注
此版本通过训练驱动版本管理系统自动管理。
""")
    
    def simulate_training_completion(self, model_name=None):
        """模拟训练完成，创建新版本"""
        if not model_name:
            model_name = f"20250623-{datetime.now().strftime('%H%M%S')}-test-model.tar.gz"
        
        print(f"=== 模拟训练完成：{model_name} ===")
        
        # 从模型名提取版本信息
        name_parts = model_name.replace('.tar.gz', '').split('-')
        if len(name_parts) >= 2:
            time_str = f"{name_parts[0]}-{name_parts[1]}"
            try:
                model_time = datetime.strptime(time_str, "%Y%m%d-%H%M%S")
                version_name = model_time.strftime("%Y%m%d%H%M_data_config")
            except:
                version_name = f"{datetime.now().strftime('%Y%m%d%H%M')}_data_config"
        else:
            version_name = f"{datetime.now().strftime('%Y%m%d%H%M')}_data_config"
        
        # 创建版本快照
        version_dir = self.versions_dir / version_name
        version_dir.mkdir(exist_ok=True)
        
        print(f"📸 创建配置快照: {version_name}")
        
        # 复制当前配置到版本
        for config_file in self.config_files:
            if config_file == 'config.yml':
                src = self.project_root / config_file
            else:
                src = self.data_dir / config_file
            
            if src.exists():
                dst = version_dir / config_file
                shutil.copy2(src, dst)
                print(f"   ✅ 快照: {config_file}")
        
        # 创建版本信息
        model_info = {
            'file': model_name,
            'time': datetime.now(),
            'version_name': version_name
        }
        self._create_version_info(version_dir, model_info, "训练完成时自动创建")
        
        print(f"✅ 训练版本创建完成: {version_name}")
        print(f"📁 data文件夹保持为工作区，可继续修改")
        
        return version_name

def main():
    print("训练驱动的版本管理系统")
    print("=" * 50)
    
    manager = TrainingDrivenManager()
    
    while True:
        print("\n=== 训练驱动版本管理 ===")
        print("1. 分析版本与模型一致性")
        print("2. 清理多余版本")
        print("3. 补充缺失版本")
        print("4. 模拟训练完成")
        print("5. 重新整理为训练驱动模式")
        print("6. 退出")
        
        choice = input("\n选择 (1-6): ").strip()
        
        if choice == '1':
            consistent, models, versions = manager.analyze_version_model_consistency()
            
        elif choice == '2':
            consistent, models, versions = manager.analyze_version_model_consistency()
            manager.cleanup_extra_versions(models, versions)
            
        elif choice == '3':
            consistent, models, versions = manager.analyze_version_model_consistency()
            manager.create_missing_versions(models, versions)
            
        elif choice == '4':
            model_name = input("输入模型名称（回车使用默认）: ").strip()
            manager.simulate_training_completion(model_name if model_name else None)
            
        elif choice == '5':
            print("重新整理为训练驱动模式...")
            consistent, models, versions = manager.analyze_version_model_consistency()
            if not consistent:
                manager.cleanup_extra_versions(models, versions)
                manager.create_missing_versions(models, versions)
            print("✅ 整理完成")
            
        elif choice == '6':
            break
        
        else:
            print("无效选择")

if __name__ == "__main__":
    main() 