#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版Excel到JSON转换器
包含槽位和实体信息处理
"""

import pandas as pd
import json
import re
from collections import defaultdict

class SlotEntityProcessor:
    """槽位和实体处理器"""
    
    def __init__(self, slot_file):
        self.slot_file = slot_file
        self.slot_entities = {}
        self.entity_mapping = {}
        self._load_slot_data()
    
    def _load_slot_data(self):
        """加载槽位数据"""
        try:
            df_slot = pd.read_excel(self.slot_file, engine='openpyxl')
            
            current_slot = None
            for _, row in df_slot.iterrows():
                if pd.notna(row['词槽名称']):
                    current_slot = row['词槽名称']
                    if current_slot not in self.slot_entities:
                        self.slot_entities[current_slot] = []
                
                if current_slot and pd.notna(row['实体标准名']):
                    entity_info = {
                        'id': int(row['实体ID']) if pd.notna(row['实体ID']) else None,
                        'value': str(row['实体标准名']),
                        'synonyms': []
                    }
                    
                    # 处理别名
                    if pd.notna(row['实体别名']):
                        aliases = str(row['实体别名']).split('==')
                        entity_info['synonyms'] = [alias.strip() for alias in aliases if alias.strip()]
                    
                    self.slot_entities[current_slot].append(entity_info)
                    
                    # 建立实体映射
                    self.entity_mapping[entity_info['value']] = {
                        'slot': current_slot,
                        'value': entity_info['value'],
                        'synonyms': entity_info['synonyms']
                    }
                    
                    # 为每个别名也建立映射
                    for synonym in entity_info['synonyms']:
                        self.entity_mapping[synonym] = {
                            'slot': current_slot,
                            'value': entity_info['value'],
                            'synonyms': entity_info['synonyms']
                        }
            
            print(f"成功加载 {len(self.slot_entities)} 个槽位，{len(self.entity_mapping)} 个实体映射")
            
        except Exception as e:
            print(f"加载槽位数据时出错: {e}")
            self.slot_entities = {}
            self.entity_mapping = {}
    
    def extract_entities_from_text(self, text):
        """从文本中提取实体标注"""
        # 匹配 [槽位名称] 格式
        slot_pattern = re.compile(r'\[([^\]]+)\]')
        entities = []
        
        matches = slot_pattern.finditer(text)
        for match in matches:
            slot_name = match.group(1)
            start = match.start()
            end = match.end()
            
            entities.append({
                'start': start,
                'end': end,
                'value': slot_name,
                'entity': slot_name
            })
        
        return entities
    
    def process_training_example(self, text):
        """处理训练样例，提取实体信息"""
        entities = self.extract_entities_from_text(text)
        
        # 移除标注符号，生成干净的文本
        clean_text = re.sub(r'\[([^\]]+)\]', r'\1', text)
        
        # 调整实体位置（因为移除了方括号）
        adjusted_entities = []
        offset = 0
        
        for entity in entities:
            # 计算移除方括号后的位置
            new_start = entity['start'] - offset
            new_end = entity['end'] - offset - 2  # 减去两个方括号
            
            adjusted_entities.append({
                'start': new_start,
                'end': new_end,
                'value': entity['value'],
                'entity': entity['entity']
            })
            
            offset += 2  # 每个实体移除了两个方括号
        
        return clean_text, adjusted_entities

def excel_to_json_enhanced(command_file, slot_file, output_file):
    """增强版Excel到JSON转换"""
    
    # 初始化槽位处理器
    slot_processor = SlotEntityProcessor(slot_file)
    
    # 读取指令Excel文件
    df_command = pd.read_excel(command_file, engine='openpyxl')
    
    # 准备存储结果
    intents_list = []
    entities_list = []
    slots_dict = {}
    
    # 构建实体和槽位信息
    for slot_name, entities in slot_processor.slot_entities.items():
        # 添加到槽位字典
        slots_dict[slot_name] = {
            'type': 'categorical',
            'values': [entity['value'] for entity in entities]
        }
        
        # 添加到实体列表
        entities_list.append({
            'entity': slot_name,
            'values': entities
        })
    
    # 处理意图数据
    current_intent = None
    
    for _, row in df_command.iterrows():
        # 检查是否是新意图
        if pd.notna(row["指令标识"]):
            # 保存上一个意图
            if current_intent is not None:
                intents_list.append(current_intent)
            
            # 创建新意图
            current_intent = {
                "intent_name": str(row["指令标识"]),
                "description": str(row["指令名称"]) if pd.notna(row["指令名称"]) else "",
                "utterances": [],
                "responses": [],
                "entities": [],
                "slots": []
            }
            
            # 添加关联词槽信息
            if pd.notna(row["关联词槽"]):
                related_slots = str(row["关联词槽"]).split(',')
                for slot in related_slots:
                    slot = slot.strip()
                    if slot and slot in slot_processor.slot_entities:
                        current_intent["slots"].append(slot)
            
            # 添加响应话术
            if pd.notna(row["执行成功话术"]):
                current_intent["responses"].append({
                    "type": "success",
                    "text": str(row["执行成功话术"])
                })
            
            if pd.notna(row["执行失败话术"]):
                current_intent["responses"].append({
                    "type": "fail",
                    "text": str(row["执行失败话术"])
                })
        
        # 处理相似问（包含实体标注）
        if current_intent is not None and pd.notna(row["相似问"]):
            utterance_raw = str(row["相似问"])
            
            # 支持逗号分隔的多个问句
            similarities = utterance_raw.split(",")
            for similarity in similarities:
                similarity = similarity.strip()
                if similarity:
                    # 处理实体标注
                    clean_text, entities = slot_processor.process_training_example(similarity)
                    
                    utterance_data = {
                        "text": clean_text,
                        "entities": entities
                    }
                    
                    current_intent["utterances"].append(utterance_data)
                    
                    # 收集该意图使用的实体类型
                    for entity in entities:
                        if entity['entity'] not in current_intent["entities"]:
                            current_intent["entities"].append(entity['entity'])
    
    # 添加最后一个意图
    if current_intent is not None:
        intents_list.append(current_intent)
    
    # 构建完整的JSON结构
    result = {
        "intents": intents_list,
        "entities": entities_list,
        "slots": slots_dict,
        "metadata": {
            "total_intents": len(intents_list),
            "total_entities": len(entities_list),
            "total_slots": len(slots_dict),
            "total_utterances": sum(len(intent["utterances"]) for intent in intents_list)
        }
    }
    
    # 写入JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 打印统计信息
    print(f"\n转换完成！")
    print(f"总意图数: {result['metadata']['total_intents']}")
    print(f"总实体类型数: {result['metadata']['total_entities']}")
    print(f"总槽位数: {result['metadata']['total_slots']}")
    print(f"总训练语句数: {result['metadata']['total_utterances']}")
    
    # 打印一些示例
    print(f"\n实体类型示例:")
    for entity in entities_list[:3]:
        print(f"  - {entity['entity']}: {len(entity['values'])} 个值")
        for value in entity['values'][:2]:
            print(f"    * {value['value']} (别名: {', '.join(value['synonyms'][:3])})")
    
    return result

if __name__ == "__main__":
    command_file = "command_403_1750175580.xlsx"
    slot_file = "slot_403_1750302057.xlsx"
    output_file = "intents_enhanced.json"
    
    try:
        result = excel_to_json_enhanced(command_file, slot_file, output_file)
        print(f"\n成功生成增强版JSON文件: {output_file}")
    except Exception as e:
        print(f"转换过程中出错: {e}")
        import traceback
        traceback.print_exc() 