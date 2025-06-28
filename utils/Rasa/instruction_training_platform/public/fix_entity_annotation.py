#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复实体标注问题的脚本
将 [占位符](占位符) 格式修复为 [具体值](实体类型) 格式
"""

import json
import yaml
import os
import pandas as pd
import re
from itertools import cycle

def load_slot_mapping():
    """加载槽位映射数据"""
    slot_file = "403/slot_403_1750302057.xlsx"
    
    try:
        df = pd.read_excel(slot_file, engine='openpyxl')
        slot_mapping = {}
        
        current_slot = None
        for _, row in df.iterrows():
            if pd.notna(row['词槽名称']):
                current_slot = row['词槽名称']
                slot_mapping[current_slot] = []
            
            if current_slot and pd.notna(row['实体标准名']):
                entity_value = str(row['实体标准名'])
                
                # 添加主要值
                slot_mapping[current_slot].append(entity_value)
                
                # 添加别名
                if pd.notna(row['实体别名']):
                    aliases = str(row['实体别名']).split('==')
                    for alias in aliases:
                        alias = alias.strip()
                        if alias:
                            slot_mapping[current_slot].append(alias)
        
        print(f"✅ 加载槽位映射成功，共 {len(slot_mapping)} 个槽位")
        for slot, values in slot_mapping.items():
            print(f"   {slot}: {len(values)} 个值")
        
        return slot_mapping
        
    except Exception as e:
        print(f"❌ 加载槽位映射失败: {e}")
        return {}

def expand_entity_placeholder(text, entity_type, slot_mapping, max_examples=10):
    """
    展开实体占位符为具体的训练样例
    
    Args:
        text: 包含占位符的文本，如 "切换[第N]个角色"
        entity_type: 实体类型，如 "第N"
        slot_mapping: 槽位映射字典
        max_examples: 每个占位符最多生成的样例数
    
    Returns:
        List[Dict]: 展开后的训练样例列表
    """
    
    if entity_type not in slot_mapping:
        # 如果找不到映射，返回原文本（移除方括号）
        clean_text = re.sub(r'\[([^\]]+)\]', r'\1', text)
        return [{
            "text": clean_text,
            "entities": []
        }]
    
    # 获取该实体类型的所有可能值
    entity_values = slot_mapping[entity_type]
    
    # 限制样例数量，避免过多
    selected_values = entity_values[:max_examples]
    
    examples = []
    
    for entity_value in selected_values:
        # 替换占位符为具体值
        expanded_text = text.replace(f"[{entity_type}]", entity_value)
        
        # 找到实体在文本中的位置
        start_pos = expanded_text.find(entity_value)
        if start_pos == -1:
            continue
            
        end_pos = start_pos + len(entity_value)
        
        example = {
            "text": expanded_text,
            "entities": [{
                "start": start_pos,
                "end": end_pos,
                "value": entity_value,
                "entity": entity_type
            }]
        }
        
        examples.append(example)
    
    return examples

def fix_training_data():
    """修复训练数据中的实体标注问题"""
    
    print("=" * 60)
    print("修复实体标注问题")
    print("=" * 60)
    
    # 加载槽位映射
    slot_mapping = load_slot_mapping()
    
    if not slot_mapping:
        print("❌ 无法加载槽位映射，退出")
        return
    
    # 加载原始意图数据
    intents_file = "intents.json"
    try:
        with open(intents_file, 'r', encoding='utf-8') as f:
            intents_data = json.load(f)
        print(f"✅ 加载原始数据: {len(intents_data['intents'])} 个意图")
    except Exception as e:
        print(f"❌ 无法加载原始数据: {e}")
        return
    
    # 修复后的数据
    fixed_intents = []
    total_original_utterances = 0
    total_fixed_utterances = 0
    
    for intent in intents_data['intents']:
        intent_name = intent['intent_name']
        original_utterances = intent.get('utterances', [])
        total_original_utterances += len(original_utterances)
        
        fixed_utterances = []
        used_entities = set()
        
        for utterance_text in original_utterances:
            # 检查是否包含实体占位符
            entity_pattern = re.compile(r'\[([^\]]+)\]')
            matches = entity_pattern.findall(utterance_text)
            
            if matches:
                # 有实体占位符，需要展开
                for entity_type in matches:
                    if entity_type in slot_mapping:
                        used_entities.add(entity_type)
                        # 展开为具体的训练样例
                        expanded_examples = expand_entity_placeholder(
                            utterance_text, entity_type, slot_mapping, max_examples=3
                        )
                        fixed_utterances.extend(expanded_examples)
                        break  # 只处理第一个占位符
                else:
                    # 没有找到匹配的实体类型，移除方括号
                    clean_text = re.sub(r'\[([^\]]+)\]', r'\1', utterance_text)
                    fixed_utterances.append({
                        "text": clean_text,
                        "entities": []
                    })
            else:
                # 没有实体占位符，直接添加
                fixed_utterances.append({
                    "text": utterance_text,
                    "entities": []
                })
        
        total_fixed_utterances += len(fixed_utterances)
        
        # 构建修复后的意图
        fixed_intent = {
            "intent_name": intent_name,
            "description": intent.get('description', ''),
            "utterances": fixed_utterances,
            "responses": intent.get('responses', []),
            "entities": list(used_entities),
            "slots": list(used_entities)
        }
        
        fixed_intents.append(fixed_intent)
        
        print(f"  {intent_name}: {len(original_utterances)} → {len(fixed_utterances)} 个样例")
    
    # 构建完整的修复后数据
    fixed_data = {
        "intents": fixed_intents,
        "entities": [{"entity": entity_type, "values": slot_mapping[entity_type]} 
                    for entity_type in slot_mapping.keys()],
        "slots": {entity_type: {"type": "categorical", "values": values} 
                 for entity_type, values in slot_mapping.items()},
        "metadata": {
            "total_intents": len(fixed_intents),
            "total_entities": len(slot_mapping),
            "total_slots": len(slot_mapping),
            "total_utterances": total_fixed_utterances,
            "original_utterances": total_original_utterances
        }
    }
    
    # 保存修复后的数据
    output_file = "intents_fixed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 修复完成！")
    print(f"   原始训练样例: {total_original_utterances}")
    print(f"   修复后样例: {total_fixed_utterances}")
    print(f"   输出文件: {output_file}")
    
    return fixed_data

def generate_fixed_rasa_data():
    """基于修复后的数据生成Rasa训练文件"""
    
    # 加载修复后的数据
    try:
        with open("intents_fixed.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 无法加载修复后的数据: {e}")
        return
    
    print(f"\n生成修复后的Rasa训练文件...")
    
    # 生成NLU数据
    nlu_data = {
        'version': '3.1',
        'nlu': []
    }
    
    for intent in data['intents']:
        intent_name = intent['intent_name']
        
        examples = []
        for utterance in intent['utterances']:
            if utterance['entities']:
                # 有实体的样例
                text = utterance['text']
                entities_text = ""
                
                sorted_entities = sorted(utterance['entities'], key=lambda x: x['start'])
                
                current_pos = 0
                for entity in sorted_entities:
                    # 添加实体前的文本
                    if entity['start'] > current_pos:
                        entities_text += text[current_pos:entity['start']]
                    
                    # 添加实体标注
                    entity_text = text[entity['start']:entity['end']]
                    entities_text += f"[{entity_text}]({entity['entity']})"
                    
                    current_pos = entity['end']
                
                # 添加剩余文本
                if current_pos < len(text):
                    entities_text += text[current_pos:]
                
                examples.append(f"- {entities_text}")
            else:
                # 没有实体的样例
                examples.append(f"- {utterance['text']}")
        
        if examples:
            nlu_data['nlu'].append({
                'intent': intent_name,
                'examples': '\n'.join(examples)
            })
    
    # 生成Domain数据
    domain_data = {
        'version': '3.1',
        'intents': [intent['intent_name'] for intent in data['intents']],
        'entities': list(data['slots'].keys()),
        'slots': {},
        'responses': {}
    }
    
    # 添加槽位定义
    for slot_name, slot_info in data['slots'].items():
        domain_data['slots'][slot_name] = {
            'type': 'categorical',
            'values': slot_info['values'],
            'mappings': [
                {
                    'type': 'from_entity',
                    'entity': slot_name
                }
            ]
        }
    
    # 添加响应
    for intent in data['intents']:
        intent_name = intent['intent_name']
        response_key = f"utter_{intent_name}"
        
        responses = []
        for response in intent['responses']:
            if response['type'] == 'success':
                responses.append({'text': response['text']})
        
        if not responses:
            responses.append({'text': f"已执行{intent.get('description', intent_name)}"})
        
        domain_data['responses'][response_key] = responses
    
    # 保存文件
    output_dir = "../rasa/data"
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存NLU文件
    with open(os.path.join(output_dir, "nlu_fixed.yml"), 'w', encoding='utf-8') as f:
        yaml.dump(nlu_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    # 保存Domain文件
    with open(os.path.join(output_dir, "domain_fixed.yml"), 'w', encoding='utf-8') as f:
        yaml.dump(domain_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"✅ 生成修复后的Rasa文件:")
    print(f"   - {os.path.join(output_dir, 'nlu_fixed.yml')}")
    print(f"   - {os.path.join(output_dir, 'domain_fixed.yml')}")
    
    # 显示修复效果示例
    print(f"\n📋 修复效果示例:")
    for intent in data['intents'][:3]:
        if intent['entities']:
            print(f"  意图: {intent['intent_name']}")
            for utterance in intent['utterances'][:2]:
                if utterance['entities']:
                    entity_info = utterance['entities'][0]
                    print(f"    ✅ {utterance['text']} -> [{entity_info['value']}]({entity_info['entity']})")

if __name__ == "__main__":
    # 修复训练数据
    fix_training_data()
    
    # 生成修复后的Rasa训练文件
    generate_fixed_rasa_data()
 