#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版Rasa训练数据生成器
支持实体和槽位信息
"""

import json
import yaml
import os
from datetime import datetime

def load_enhanced_intents(json_file):
    """加载增强版意图数据"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"加载JSON文件失败: {e}")
        return None

def generate_nlu_data(intents_data):
    """生成NLU训练数据"""
    nlu_data = {
        'version': '3.1',
        'nlu': []
    }
    
    for intent in intents_data['intents']:
        intent_name = intent['intent_name']
        
        # 构建训练样例
        examples = []
        for utterance in intent['utterances']:
            if utterance['entities']:
                # 有实体标注的样例
                text = utterance['text']
                entities_text = ""
                
                # 按位置排序实体
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
    
    return nlu_data

def generate_domain_data(intents_data):
    """生成Domain数据"""
    domain_data = {
        'version': '3.1',
        'intents': [],
        'entities': [],
        'slots': {},
        'responses': {}
    }
    
    # 添加意图
    for intent in intents_data['intents']:
        domain_data['intents'].append(intent['intent_name'])
    
    # 添加实体
    for entity in intents_data['entities']:
        domain_data['entities'].append(entity['entity'])
    
    # 添加槽位
    for slot_name, slot_info in intents_data['slots'].items():
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
    for intent in intents_data['intents']:
        intent_name = intent['intent_name']
        response_key = f"utter_{intent_name}"
        
        responses = []
        for response in intent['responses']:
            if response['type'] == 'success':
                responses.append({'text': response['text']})
        
        if not responses:
            # 如果没有成功响应，添加默认响应
            responses.append({'text': f"已执行{intent.get('description', intent_name)}"})
        
        domain_data['responses'][response_key] = responses
    
    return domain_data

def generate_rules_data(intents_data):
    """生成Rules数据（单轮对话规则）"""
    rules_data = {
        'version': '3.1',
        'rules': []
    }
    
    for intent in intents_data['intents']:
        intent_name = intent['intent_name']
        rule_name = f"Rule for {intent_name}"
        
        rule = {
            'rule': rule_name,
            'steps': [
                {'intent': intent_name},
                {'action': f"utter_{intent_name}"}
            ]
        }
        
        rules_data['rules'].append(rule)
    
    return rules_data

def generate_config_data():
    """生成优化的配置数据（专注于单轮对话，不使用stories）"""
    config_data = {
        'recipe': 'default.v1',
        'language': 'zh',
        'pipeline': [
            {'name': 'JiebaTokenizer'},
            {'name': 'RegexFeaturizer'},
            {'name': 'LexicalSyntacticFeaturizer'},
            {
                'name': 'CountVectorsFeaturizer',
                'analyzer': 'char_wb',
                'min_ngram': 1,
                'max_ngram': 4
            },
            {
                'name': 'CountVectorsFeaturizer',
                'analyzer': 'word',
                'min_ngram': 1,
                'max_ngram': 2
            },
            {
                'name': 'DIETClassifier',
                'epochs': 200,
                'entity_recognition': True,
                'intent_classification': True,
                'use_masked_language_model': True,
                'transformer_size': 256,
                'number_of_transformer_layers': 2,
                'number_of_attention_heads': 4,
                'batch_size': 64,
                'evaluate_every_number_of_epochs': 20,
                'evaluate_on_number_of_examples': 0,
                'tensorboard_log_directory': './tensorboard',
                'tensorboard_log_level': 'epoch'
            },
            {
                'name': 'EntitySynonymMapper'
            },
            {
                'name': 'ResponseSelector',
                'epochs': 100,
                'retrieval_intent': None
            }
        ],
        'policies': [
            {
                'name': 'RulePolicy',
                'core_fallback_threshold': 0.3,
                'core_fallback_action_name': 'action_default_fallback',
                'enable_fallback_prediction': True
            },
            {
                'name': 'UnexpecTEDIntentPolicy',
                'max_history': 5,
                'epochs': 100,
                'batch_size': 32
            },
            {
                'name': 'TEDPolicy',
                'max_history': 5,
                'epochs': 100,
                'batch_size': 32,
                'evaluate_every_number_of_epochs': 20,
                'evaluate_on_number_of_examples': 0
            }
        ]
    }
    
    return config_data

def save_yaml_file(data, file_path):
    """保存YAML文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"✅ 生成文件: {file_path}")
        return True
    except Exception as e:
        print(f"❌ 生成文件失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("增强版Rasa训练数据生成器")
    print("支持实体和槽位信息")
    print("=" * 60)
    
    # 输入输出文件路径
    input_file = "intents_enhanced.json"
    output_dir = "../rasa/data"
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载增强版意图数据
    print(f"📖 加载数据文件: {input_file}")
    intents_data = load_enhanced_intents(input_file)
    
    if not intents_data:
        print("❌ 无法加载数据文件，退出")
        return
    
    # 打印数据统计
    print(f"\n📊 数据统计:")
    print(f"   意图数量: {intents_data['metadata']['total_intents']}")
    print(f"   实体类型: {intents_data['metadata']['total_entities']}")
    print(f"   槽位数量: {intents_data['metadata']['total_slots']}")
    print(f"   训练语句: {intents_data['metadata']['total_utterances']}")
    
    print(f"\n🏗️ 生成Rasa训练文件...")
    
    # 生成各种数据文件
    success_count = 0
    
    # 1. 生成NLU数据
    print(f"\n1. 生成NLU数据...")
    nlu_data = generate_nlu_data(intents_data)
    if save_yaml_file(nlu_data, os.path.join(output_dir, "nlu.yml")):
        success_count += 1
        print(f"   包含 {len(nlu_data['nlu'])} 个意图")
    
    # 2. 生成Domain数据
    print(f"\n2. 生成Domain数据...")
    domain_data = generate_domain_data(intents_data)
    if save_yaml_file(domain_data, os.path.join(output_dir, "domain.yml")):
        success_count += 1
        print(f"   包含 {len(domain_data['intents'])} 个意图")
        print(f"   包含 {len(domain_data['entities'])} 个实体类型")
        print(f"   包含 {len(domain_data['slots'])} 个槽位")
        print(f"   包含 {len(domain_data['responses'])} 个响应模板")
    
    # 3. 生成Rules数据（单轮对话）
    print(f"\n3. 生成Rules数据（单轮对话）...")
    rules_data = generate_rules_data(intents_data)
    if save_yaml_file(rules_data, os.path.join(output_dir, "rules.yml")):
        success_count += 1
        print(f"   包含 {len(rules_data['rules'])} 条规则")
    
    # 4. 生成配置文件
    print(f"\n4. 生成配置文件...")
    config_data = generate_config_data()
    if save_yaml_file(config_data, "../rasa/config.yml"):
        success_count += 1
        print(f"   优化单轮对话配置")
    
    # 删除stories.yml文件（因为我们专注于单轮对话）
    stories_file = os.path.join(output_dir, "stories.yml")
    if os.path.exists(stories_file):
        try:
            os.remove(stories_file)
            print(f"🗑️ 删除stories.yml文件（专注单轮对话）")
        except Exception as e:
            print(f"⚠️ 删除stories.yml失败: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"🎉 生成完成！成功生成 {success_count}/4 个文件")
    print(f"📁 输出目录: {output_dir}")
    print(f"⚡ 配置专注于单轮对话，无需stories.yml")
    print(f"🚀 现在可以运行: cd ../rasa && rasa train --force")
    print("=" * 60)
    
    # 打印实体和槽位信息
    print(f"\n📋 实体和槽位详情:")
    for entity in intents_data['entities']:
        entity_name = entity['entity']
        entity_count = len(entity['values'])
        print(f"   🏷️ {entity_name}: {entity_count} 个值")
        
        # 显示前3个值作为示例
        for i, value in enumerate(entity['values'][:3]):
            synonyms_info = f" (别名: {', '.join(value['synonyms'][:3])})" if value['synonyms'] else ""
            print(f"      • {value['value']}{synonyms_info}")
        
        if entity_count > 3:
            print(f"      ... 还有 {entity_count - 3} 个值")
    
    print(f"\n🎯 意图与槽位关联:")
    for intent in intents_data['intents']:
        if intent['entities']:
            print(f"   {intent['intent_name']}: {', '.join(intent['entities'])}")

if __name__ == "__main__":
    main() 