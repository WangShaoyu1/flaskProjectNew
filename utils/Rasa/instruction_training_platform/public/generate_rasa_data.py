#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从intents.json生成Rasa训练数据
"""

import json
import yaml
import os
from typing import Dict, List, Any

def load_intents_data(file_path: str) -> Dict[str, Any]:
    """加载意图数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_nlu_data(intents_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成NLU训练数据"""
    nlu_data = {
        'version': '3.1',
        'nlu': []
    }
    
    for intent in intents_data['intents']:
        intent_name = intent['intent_name']
        utterances = intent.get('utterances', [])
        
        if utterances:
            examples = []
            for utterance in utterances:
                examples.append(f"- {utterance}")
            
            nlu_data['nlu'].append({
                'intent': intent_name,
                'examples': '\n'.join(examples)
            })
    
    return nlu_data

def generate_domain_data(intents_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成Domain配置"""
    domain_data = {
        'version': '3.1',
        'intents': [],
        'entities': [],
        'slots': {},
        'responses': {},
        'actions': [],
        'forms': {},
        'e2e_actions': [],
        'session_config': {
            'session_expiration_time': 60,
            'carry_over_slots_to_new_session': True
        }
    }
    
    # 添加意图
    for intent in intents_data['intents']:
        intent_name = intent['intent_name']
        domain_data['intents'].append(intent_name)
        
        # 添加响应
        responses = intent.get('responses', [])
        response_key = f"utter_{intent_name}"
        domain_data['responses'][response_key] = []
        
        if responses:
            for response in responses:
                domain_data['responses'][response_key].append({
                    'text': response['text']
                })
        else:
            # 如果没有响应，添加默认响应
            domain_data['responses'][response_key].append({
                'text': f"好的，我理解您的{intent.get('description', intent_name)}请求。"
            })
    
    return domain_data

def generate_rules_data(intents_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成Rules配置"""
    rules = []
    
    # 为每个意图生成基本规则
    for intent in intents_data['intents']:
        intent_name = intent['intent_name']
        rules.append({
            'rule': f'Respond to {intent_name}',
            'steps': [
                {'intent': intent_name},
                {'action': f'utter_{intent_name}'}
            ]
        })
    
    return {
        'version': '3.1',
        'rules': rules
    }

def generate_stories_data(intents_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成Stories配置"""
    stories = []
    
    # 生成基本故事
    for intent in intents_data['intents']:
        intent_name = intent['intent_name']
        stories.append({
            'story': f'{intent_name} story',
            'steps': [
                {'intent': intent_name},
                {'action': f'utter_{intent_name}'}
            ]
        })
    
    return {
        'version': '3.1',
        'stories': stories
    }

def save_yaml_file(data: Dict[str, Any], file_path: str):
    """保存YAML文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

def main():
    """主函数"""
    # 文件路径
    intents_file = 'intents.json'
    rasa_dir = '../rasa/data'
    
    # 检查输入文件
    if not os.path.exists(intents_file):
        print(f"错误: 找不到文件 {intents_file}")
        return
    
    print("正在加载意图数据...")
    intents_data = load_intents_data(intents_file)
    print(f"加载了 {len(intents_data['intents'])} 个意图")
    
    # 生成NLU数据
    print("生成NLU训练数据...")
    nlu_data = generate_nlu_data(intents_data)
    nlu_file = os.path.join(rasa_dir, 'nlu.yml')
    save_yaml_file(nlu_data, nlu_file)
    print(f"NLU数据已保存到: {nlu_file}")
    
    # 生成Domain数据
    print("生成Domain配置...")
    domain_data = generate_domain_data(intents_data)
    domain_file = os.path.join(rasa_dir, 'domain.yml')
    save_yaml_file(domain_data, domain_file)
    print(f"Domain配置已保存到: {domain_file}")
    
    # 生成Rules数据
    print("生成Rules配置...")
    rules_data = generate_rules_data(intents_data)
    rules_file = os.path.join(rasa_dir, 'rules.yml')
    save_yaml_file(rules_data, rules_file)
    print(f"Rules配置已保存到: {rules_file}")
    
    # 生成Stories数据
    print("生成Stories配置...")
    stories_data = generate_stories_data(intents_data)
    stories_file = os.path.join(rasa_dir, 'stories_new.yml')
    save_yaml_file(stories_data, stories_file)
    print(f"Stories配置已保存到: {stories_file}")
    
    print("✅ Rasa训练数据生成完成!")
    
    # 统计信息
    total_utterances = sum(len(intent.get('utterances', [])) for intent in intents_data['intents'])
    total_responses = sum(len(intent.get('responses', [])) for intent in intents_data['intents'])
    
    print(f"""
📊 数据统计:
- 意图数量: {len(intents_data['intents'])}
- 训练语句: {total_utterances}
- 响应模板: {total_responses}
- 规则数量: {len(intents_data['intents'])}
- 故事数量: {len(intents_data['intents'])}
    """)

if __name__ == "__main__":
    main() 