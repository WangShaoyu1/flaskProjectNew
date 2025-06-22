#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Slot映射验证工具

用于验证domain.yml中的slot定义与映射表的一致性
确保所有中英文映射关系正确
"""

import yaml
import os
import sys
from typing import Dict, List, Set

def load_domain_yml(file_path: str) -> Dict:
    """加载domain.yml文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 无法加载domain.yml: {e}")
        return {}

def extract_slots_from_domain(domain_data: Dict) -> Dict[str, Dict]:
    """从domain数据中提取slot信息"""
    slots = {}
    if 'slots' in domain_data:
        for slot_name, slot_config in domain_data['slots'].items():
            slots[slot_name] = {
                'type': slot_config.get('type', 'unknown'),
                'values': slot_config.get('values', []),
                'entity': None
            }
            
            # 提取entity映射
            if 'mappings' in slot_config:
                for mapping in slot_config['mappings']:
                    if mapping.get('type') == 'from_entity':
                        slots[slot_name]['entity'] = mapping.get('entity')
                        break
    
    return slots

def get_expected_mappings() -> Dict[str, str]:
    """获取预期的中英文映射关系"""
    return {
        'portion': '份量',
        'sleep_time': '休眠时间', 
        'taste': '口感',
        'category': '品类',
        'broadcast_mode': '播报模式',
        'power': '火力',
        'number': '第N',
        'confirm': '肯否判断',
        'dish_name': '菜品名称',
        'page_name': '页面名称'
    }

def validate_slot_mappings(slots: Dict[str, Dict], expected_mappings: Dict[str, str]) -> List[str]:
    """验证slot映射关系"""
    issues = []
    
    # 检查预期的映射是否都存在
    for english_name, chinese_name in expected_mappings.items():
        if english_name not in slots:
            issues.append(f"❌ 缺少slot定义: {english_name} ({chinese_name})")
        else:
            slot_info = slots[english_name]
            if slot_info['entity'] != chinese_name:
                issues.append(f"❌ Entity映射错误: {english_name} -> {slot_info['entity']}, 预期: {chinese_name}")
    
    # 检查是否有未映射的slot
    for slot_name in slots:
        if slot_name not in expected_mappings:
            issues.append(f"⚠️  未在映射表中定义的slot: {slot_name}")
    
    return issues

def generate_mapping_report(slots: Dict[str, Dict], expected_mappings: Dict[str, str]) -> str:
    """生成映射关系报告"""
    report = []
    report.append("# Slot映射关系验证报告")
    report.append("")
    report.append("## 当前映射状态")
    report.append("")
    
    for english_name, chinese_name in expected_mappings.items():
        if english_name in slots:
            slot_info = slots[english_name]
            status = "✅" if slot_info['entity'] == chinese_name else "❌"
            report.append(f"- {status} `{english_name}` → `{slot_info['entity']}` (预期: `{chinese_name}`)")
        else:
            report.append(f"- ❌ `{english_name}` → 未定义 (预期: `{chinese_name}`)")
    
    report.append("")
    report.append("## 详细信息")
    report.append("")
    
    for english_name in sorted(slots.keys()):
        slot_info = slots[english_name]
        chinese_name = expected_mappings.get(english_name, "未映射")
        
        report.append(f"### {english_name}")
        report.append(f"- **中文名称**: {chinese_name}")
        report.append(f"- **Entity映射**: {slot_info['entity']}")
        report.append(f"- **类型**: {slot_info['type']}")
        report.append(f"- **值数量**: {len(slot_info['values'])}")
        if slot_info['values'] and len(slot_info['values']) <= 10:
            report.append(f"- **示例值**: {', '.join(slot_info['values'][:5])}")
        report.append("")
    
    return "\\n".join(report)

def main():
    """主函数"""
    print("🔍 Slot映射验证工具")
    print("=" * 50)
    
    # 检查文件路径
    domain_path = os.path.join('rasa', 'data', 'domain.yml')
    if not os.path.exists(domain_path):
        print(f"❌ 找不到domain.yml文件: {domain_path}")
        sys.exit(1)
    
    # 加载domain文件
    print(f"📂 加载domain文件: {domain_path}")
    domain_data = load_domain_yml(domain_path)
    if not domain_data:
        sys.exit(1)
    
    # 提取slot信息
    slots = extract_slots_from_domain(domain_data)
    print(f"📊 发现 {len(slots)} 个slot定义")
    
    # 获取预期映射
    expected_mappings = get_expected_mappings()
    print(f"📋 预期映射关系: {len(expected_mappings)} 个")
    
    # 验证映射关系
    print("\\n🔍 验证映射关系...")
    issues = validate_slot_mappings(slots, expected_mappings)
    
    if not issues:
        print("✅ 所有映射关系验证通过！")
    else:
        print("⚠️  发现以下问题:")
        for issue in issues:
            print(f"  {issue}")
    
    # 生成报告
    print("\\n📝 生成详细报告...")
    report = generate_mapping_report(slots, expected_mappings)
    
    # 保存报告
    report_path = 'tools/slot_mapping_validation_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 报告已保存到: {report_path}")
    
    # 返回状态码
    return 0 if not issues else 1

if __name__ == "__main__":
    sys.exit(main()) 