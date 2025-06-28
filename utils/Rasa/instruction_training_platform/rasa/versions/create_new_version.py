#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rasa配置文件版本管理工具
自动创建新版本并归档配置文件
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def create_new_version():
    """创建新的配置版本"""
    
    # 获取当前时间
    now = datetime.now()
    version_name = now.strftime("%Y%m%d%H%M_data_config")
    
    print(f"=== 创建新版本: {version_name} ===")
    
    # 项目根目录
    project_root = Path(__file__).parent.parent
    versions_dir = Path(__file__).parent
    
    # 创建版本文件夹
    new_version_dir = versions_dir / version_name
    new_version_dir.mkdir(exist_ok=True)
    
    print(f"创建版本文件夹: {new_version_dir}")
    
    # 复制配置文件
    config_files = {
        'config.yml': project_root / 'config.yml',
        'domain.yml': project_root / 'data' / 'domain.yml',
        'nlu.yml': project_root / 'data' / 'nlu.yml',
        'rules.yml': project_root / 'data' / 'rules.yml'
    }
    
    for target_name, source_path in config_files.items():
        if source_path.exists():
            target_path = new_version_dir / target_name
            shutil.copy2(source_path, target_path)
            print(f"复制文件: {source_path} -> {target_path}")
        else:
            print(f"⚠️  文件不存在: {source_path}")
    
    # 创建版本说明文件
    version_info = new_version_dir / 'version_info.md'
    with open(version_info, 'w', encoding='utf-8') as f:
        f.write(f"""# 版本信息 - {version_name}

## 创建时间
{now.strftime("%Y-%m-%d %H:%M:%S")}

## 配置文件来源
- config.yml: rasa/config.yml
- domain.yml: rasa/data/domain.yml  
- nlu.yml: rasa/data/nlu.yml
- rules.yml: rasa/data/rules.yml

## 版本说明
请在此处添加本版本的详细说明：
- 主要变更内容
- 更新原因
- 预期效果

## 训练计划
- [ ] 配置文件验证
- [ ] 开始模型训练
- [ ] 训练完成验证
- [ ] 性能测试
- [ ] 部署上线

## 备注
请在训练前填写完整的版本说明信息。
""")
    
    print(f"创建版本说明文件: {version_info}")
    print(f"\n✅ 版本 {version_name} 创建完成！")
    print(f"\n📝 请编辑 {version_info} 文件添加版本说明")
    print(f"📁 版本文件夹: {new_version_dir}")
    
    return version_name, new_version_dir

def list_versions():
    """列出所有版本"""
    versions_dir = Path(__file__).parent
    
    print("=== 现有版本列表 ===")
    
    version_dirs = [d for d in versions_dir.iterdir() if d.is_dir() and d.name.endswith('_data_config')]
    version_dirs.sort()
    
    if not version_dirs:
        print("暂无版本记录")
        return
    
    for i, version_dir in enumerate(version_dirs, 1):
        version_info_file = version_dir / 'version_info.md'
        
        # 获取文件夹创建时间
        try:
            create_time = datetime.fromtimestamp(version_dir.stat().st_ctime)
            time_str = create_time.strftime("%Y-%m-%d %H:%M:%S")
        except:
            time_str = "未知"
        
        print(f"{i}. {version_dir.name}")
        print(f"   创建时间: {time_str}")
        print(f"   路径: {version_dir}")
        
        # 检查文件完整性
        required_files = ['config.yml', 'domain.yml', 'nlu.yml', 'rules.yml']
        missing_files = [f for f in required_files if not (version_dir / f).exists()]
        if missing_files:
            print(f"   ⚠️  缺少文件: {', '.join(missing_files)}")
        else:
            print(f"   ✅ 文件完整")
        
        print()

def main():
    """主函数"""
    print("Rasa配置文件版本管理工具")
    print("=" * 40)
    
    while True:
        print("\n请选择操作:")
        print("1. 创建新版本")
        print("2. 查看版本列表")
        print("3. 退出")
        
        try:
            choice = input("\n请输入选择 (1-3): ").strip()
            
            if choice == '1':
                create_new_version()
            elif choice == '2':
                list_versions()
            elif choice == '3':
                print("退出程序")
                break
            else:
                print("无效选择，请重试")
                
        except KeyboardInterrupt:
            print("\n\n程序被中断退出")
            break
        except Exception as e:
            print(f"\n❌ 操作失败: {e}")

if __name__ == "__main__":
    main() 