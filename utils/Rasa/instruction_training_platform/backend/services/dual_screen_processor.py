"""
双屏数据格式处理器
支持双屏指令和词槽Excel文件的解析与RASA训练数据生成
新增：完整的追问逻辑支持
"""

import pandas as pd
import yaml
import re
import json
import os
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DualScreenProcessor:
    """双屏数据格式处理器 - 支持追问逻辑"""
    
    def __init__(self):
        self.slots_entities_map = {}  # 词槽到实体值的映射
        self.instructions = []        # 处理后的指令列表
        self.slots = []              # 处理后的词槽列表
        self.forms = []              # 表单定义列表
    
    def process_slot_data(self, excel_file: str) -> List[Dict[str, Any]]:
        """
        处理双屏词槽Excel数据
        
        Args:
            excel_file: 词槽Excel文件路径
            
        Returns:
            List[Dict]: 处理后的词槽数据列表
        """
        try:
            logger.info(f"开始处理词槽文件: {excel_file}")
            df = pd.read_excel(excel_file)
            
            slots = []
            current_slot = None
            
            for _, row in df.iterrows():
                # 新词槽开始
                if pd.notna(row['词槽名称']):
                    if current_slot:
                        slots.append(current_slot)
                        # 建立词槽实体映射
                        self.slots_entities_map[current_slot['slot_name']] = current_slot['entities']
                    
                    slot_name_en = self._generate_slot_name_en(row['词槽名称'])
                    current_slot = {
                        'slot_name': row['词槽名称'],
                        'slot_name_en': slot_name_en,
                        'description': row['词槽描述'] if pd.notna(row['词槽描述']) else '',
                        'slot_type': 'categorical',
                        'entities': []
                    }
                
                # 添加实体值
                if pd.notna(row['实体标准名']):
                    entity = {
                        'value': row['实体标准名'],
                        'synonyms': []
                    }
                    
                    # 处理别名（用==分隔）
                    if pd.notna(row['实体别名']):
                        synonyms = row['实体别名'].split('==')
                        entity['synonyms'] = [s.strip() for s in synonyms if s.strip()]
                    
                    if current_slot:
                        current_slot['entities'].append(entity)
            
            # 添加最后一个词槽
            if current_slot:
                slots.append(current_slot)
                self.slots_entities_map[current_slot['slot_name']] = current_slot['entities']
            
            self.slots = slots
            logger.info(f"词槽处理完成，共处理 {len(slots)} 个词槽")
            
            return slots
            
        except Exception as e:
            logger.error(f"处理词槽文件失败: {str(e)}")
            raise Exception(f"词槽文件处理错误: {str(e)}")
    
    def _generate_slot_name_en(self, slot_name_cn: str) -> str:
        """生成英文词槽名称"""
        # 中文到英文的映射表 - 扩展版
        mapping = {
            '休眠时间': 'sleep_time',
            '火力': 'fire_power', 
            '第N': 'sequence_number',
            '菜品名称': 'dish_name',
            '页面名称': 'page_name',
            '口感': 'taste',
            '肯否判断': 'yes_no',
            '时长': 'duration',
            '数量': 'quantity',
            '音量': 'volume',
            '时间': 'time',
            # 新增的映射
            '温度': 'temperature',
            '亮度': 'brightness',
            '模式': 'mode',
            '档位': 'level',
            '状态': 'status',
            '类型': 'type',
            '颜色': 'color',
            '大小': 'size',
            '位置': 'position',
            '方向': 'direction',
            '速度': 'speed',
            '重量': 'weight'
        }
        
        # 如果有映射，使用映射；否则生成一个基于hash的唯一名称
        if slot_name_cn in mapping:
            return mapping[slot_name_cn]
        else:
            # 生成一个基于中文名称hash的英文名称
            import hashlib
            hash_value = hashlib.md5(slot_name_cn.encode('utf-8')).hexdigest()[:8]
            return f"slot_{hash_value}"
    
    def parse_entity_annotations(self, text: str) -> List[Dict[str, Any]]:
        """
        解析相似问中的词槽标注并生成RASA实体标注格式
        
        Args:
            text: 原始相似问文本，如 "设置[火力]"
            
        Returns:
            List[Dict]: 生成的训练样本，包含实体标注
        """
        training_examples = []
        
        # 查找所有词槽标注
        slot_patterns = re.findall(r'\[([^\]]+)\]', text)
        
        if not slot_patterns:
            # 没有词槽标注，直接返回原文
            training_examples.append({'text': text, 'entities': []})
            return training_examples
        
        # 为每个词槽生成实体标注样本
        for slot_name in slot_patterns:
            if slot_name in self.slots_entities_map:
                entities = self.slots_entities_map[slot_name]
                
                # 为该词槽的每个实体值生成一个训练样本（限制数量避免过多）
                sample_entities = entities[:5] if len(entities) > 5 else entities
                
                for entity in sample_entities:
                    entity_value = entity['value']
                    
                    # 替换词槽标注为实际实体值
                    annotated_text = text.replace(f'[{slot_name}]', entity_value)
                    
                    # 生成RASA格式的实体标注
                    start_pos = annotated_text.find(entity_value)
                    end_pos = start_pos + len(entity_value)
                    
                    if start_pos != -1:
                        rasa_example = {
                            'text': annotated_text,
                            'entities': [
                                {
                                    'start': start_pos,
                                    'end': end_pos,
                                    'value': entity_value,
                                    'entity': f'entity_{self._generate_slot_name_en(slot_name)}'
                                }
                            ]
                        }
                        training_examples.append(rasa_example)
        
        return training_examples
    
    def _detect_required_slots(self, related_slots: str, similar_questions: List[str]) -> List[str]:
        """
        检测指令中的必需词槽
        
        Args:
            related_slots: 关联词槽字符串
            similar_questions: 相似问列表
            
        Returns:
            List[str]: 必需词槽列表
        """
        required_slots = []
        
        # 从关联词槽中提取
        if related_slots:
            slots_list = [s.strip() for s in related_slots.split(',') if s.strip()]
            required_slots.extend(slots_list)
        
        # 从相似问中提取带标注的词槽
        for question in similar_questions:
            slot_patterns = re.findall(r'\[([^\]]+)\]', question)
            for slot_name in slot_patterns:
                if slot_name not in required_slots:
                    required_slots.append(slot_name)
        
        return required_slots
    
    def process_instruction_data(self, excel_file: str) -> List[Dict[str, Any]]:
        """
        处理双屏指令Excel数据 - 增强版支持追问逻辑
        
        Args:
            excel_file: 指令Excel文件路径
            
        Returns:
            List[Dict]: 处理后的指令数据列表
        """
        try:
            logger.info(f"开始处理指令文件: {excel_file}")
            df = pd.read_excel(excel_file)
            
            instructions = []
            
            for instruction_id, group in df.groupby('指令标识'):
                if pd.isna(instruction_id):
                    continue
                
                # 获取指令基本信息（取第一行非空值）
                instruction_info = group.dropna(subset=['指令名称']).iloc[0]
                
                # 处理相似问，包括实体标注
                all_training_examples = []
                similar_questions = group['相似问'].dropna().unique().tolist()
                
                for similar_question in similar_questions:
                    # 解析实体标注并生成训练样本
                    examples = self.parse_entity_annotations(similar_question)
                    all_training_examples.extend(examples)
                
                # 如果没有相似问，至少要有一个基本示例
                if not all_training_examples:
                    all_training_examples.append({
                        'text': instruction_info['指令名称'],
                        'entities': []
                    })
                
                # 检测必需词槽
                related_slots = instruction_info['关联词槽'] if pd.notna(instruction_info['关联词槽']) else ''
                required_slots = self._detect_required_slots(related_slots, similar_questions)
                
                # 处理追问次数
                follow_up_times = 3  # 默认追问3次
                if pd.notna(instruction_info.get('追问次数', pd.NA)):
                    try:
                        follow_up_times = int(instruction_info['追问次数'])
                    except (ValueError, TypeError):
                        follow_up_times = 3
                
                instruction_data = {
                    'intent': instruction_id,
                    'intent_name_cn': instruction_info['指令名称'],
                    'category': instruction_info['分类'],
                    'description': instruction_info['指令描述'] if pd.notna(instruction_info['指令描述']) else '',
                    'related_slots': related_slots,
                    'required_slots': required_slots,  # 必需词槽列表
                    'training_examples': all_training_examples,
                    'success_response': instruction_info['执行成功话术'] if pd.notna(instruction_info['执行成功话术']) else '',
                    'failure_response': instruction_info['执行失败话术'] if pd.notna(instruction_info['执行失败话术']) else '',
                    'follow_up_response': instruction_info['追问话术'] if pd.notna(instruction_info['追问话术']) else '',
                    'follow_up_failure_response': instruction_info['追问失败话术'] if pd.notna(instruction_info['追问失败话术']) else '',
                    'follow_up_times': follow_up_times,  # 最大追问次数
                    'has_slot_filling': len(required_slots) > 0  # 是否需要词槽填充
                }
                
                instructions.append(instruction_data)
                
                # 如果有必需词槽，生成表单定义
                if required_slots:
                    self._generate_form_definition(instruction_data)
            
            self.instructions = instructions
            logger.info(f"指令处理完成，共处理 {len(instructions)} 个指令，其中 {sum(1 for inst in instructions if inst['has_slot_filling'])} 个需要词槽填充")
            
            return instructions
            
        except Exception as e:
            logger.error(f"处理指令文件失败: {str(e)}")
            raise Exception(f"指令文件处理错误: {str(e)}")
    
    def _generate_form_definition(self, instruction: Dict[str, Any]) -> None:
        """
        为指令生成RASA表单定义
        
        Args:
            instruction: 指令数据
        """
        if not instruction['required_slots']:
            return
        
        form_name = f"{instruction['intent']}_form"
        
        # 构建表单的必需词槽
        required_slots_mapping = {}
        for slot_name in instruction['required_slots']:
            slot_name_en = self._generate_slot_name_en(slot_name)
            required_slots_mapping[slot_name_en] = [
                {
                    'type': 'from_entity',
                    'entity': f'entity_{slot_name_en}'
                }
            ]
        
        form_definition = {
            'form_name': form_name,
            'intent': instruction['intent'],
            'required_slots': list(required_slots_mapping.keys()),
            'slots_mapping': required_slots_mapping,
            'follow_up_response': instruction['follow_up_response'],
            'follow_up_failure_response': instruction['follow_up_failure_response'],
            'follow_up_times': instruction['follow_up_times']
        }
        
        self.forms.append(form_definition)
    
    def generate_nlu_yml(self) -> str:
        """生成NLU训练数据 - 增强版包含确认和否定意图"""
        try:
            nlu_items = []
            
            # 添加意图训练数据（包含实体标注）
            for instruction in self.instructions:
                if instruction['training_examples']:
                    intent_examples = []
                    
                    for example in instruction['training_examples']:
                        text = example['text']
                        entities = example.get('entities', [])
                        
                        # 生成RASA实体标注格式
                        if entities:
                            # 按实体位置排序，从后往前插入标注避免位置偏移
                            sorted_entities = sorted(entities, key=lambda x: x['start'], reverse=True)
                            
                            for entity in sorted_entities:
                                start, end = entity['start'], entity['end']
                                entity_name = entity['entity']
                                value = entity['value']
                                
                                # 插入实体标注：[实体值](entity_name)
                                text = text[:start] + f"[{value}]({entity_name})" + text[end:]
                        
                        intent_examples.append(f"    - {text}")
                    
                    if intent_examples:
                        intent_data = {
                            'intent': instruction['intent'],
                            'examples': '|\n' + '\n'.join(intent_examples)
                        }
                        nlu_items.append(intent_data)
            
            # 添加通用意图 - 用于表单处理
            common_intents = [
                {
                    'intent': 'affirm',
                    'examples': '|\n    - 是的\n    - 对\n    - 好的\n    - 确认\n    - 正确\n    - 没错'
                },
                {
                    'intent': 'deny', 
                    'examples': '|\n    - 不是\n    - 不对\n    - 错了\n    - 不\n    - 否定\n    - 重新来'
                },
                {
                    'intent': 'inform',
                    'examples': '|\n    - 我要[火力]\n    - 选择[口感]\n    - 设置[休眠时间]'
                }
            ]
            
            nlu_items.extend(common_intents)
            
            # 添加实体同义词 - 避免重复
            added_synonyms = set()
            for slot in self.slots:
                for entity in slot['entities']:
                    if entity['synonyms'] and entity['value'] not in added_synonyms:
                        synonym_data = {
                            'synonym': entity['value'],
                            'examples': '|\n' + '\n'.join([f"    - {syn}" for syn in entity['synonyms']])
                        }
                        nlu_items.append(synonym_data)
                        added_synonyms.add(entity['value'])
            
            # 构建完整的NLU数据结构
            nlu_data = {
                'version': '3.1',
                'nlu': nlu_items
            }
            
            # 生成YAML并验证格式
            yaml_content = yaml.dump(nlu_data, allow_unicode=True, default_flow_style=False)
            
            # 验证生成的YAML格式
            try:
                parsed = yaml.safe_load(yaml_content)
                if 'nlu' not in parsed or not isinstance(parsed['nlu'], list):
                    raise ValueError("NLU格式错误：缺少nlu数组")
                    
                # 验证每个NLU项目的格式
                for item in parsed['nlu']:
                    if 'synonym' in item:
                        if 'examples' not in item:
                            raise ValueError(f"同义词格式错误：{item}")
                    elif 'intent' in item:
                        if 'examples' not in item:
                            raise ValueError(f"意图格式错误：{item}")
                    else:
                        raise ValueError(f"未知的NLU项目格式：{item}")
                        
            except yaml.YAMLError as e:
                logger.error(f"YAML格式验证失败: {e}")
                raise Exception(f"生成的YAML格式不正确: {e}")
            except ValueError as e:
                logger.error(f"NLU格式验证失败: {e}")
                raise Exception(f"NLU数据格式错误: {e}")
                
            return yaml_content
            
        except Exception as e:
            logger.error(f"生成NLU数据失败: {str(e)}")
            raise Exception(f"NLU数据生成错误: {str(e)}")
    
    def generate_domain_yml(self) -> str:
        """生成Domain配置 - 增强版包含Forms和追问响应"""
        try:
            domain_data = {
                'version': '3.1',
                'intents': [],
                'entities': [],
                'slots': {},
                'forms': {},
                'responses': {},
                'actions': [],
                'session_config': {
                    'session_expiration_time': 60,
                    'carry_over_slots_to_new_session': True
                }
            }
            
            # 添加意图
            for instruction in self.instructions:
                domain_data['intents'].append(instruction['intent'])
            
            # 添加通用意图
            domain_data['intents'].extend(['affirm', 'deny', 'inform'])
            
            # 添加实体和词槽
            for slot in self.slots:
                entity_name = f"entity_{slot['slot_name_en']}"
                domain_data['entities'].append(entity_name)
                
                # 添加词槽定义
                domain_data['slots'][slot['slot_name_en']] = {
                    'type': 'categorical',
                    'values': [entity['value'] for entity in slot['entities']],
                    'mappings': [
                        {
                            'type': 'from_entity',
                            'entity': entity_name
                        }
                    ]
                }
            
            # 添加表单定义
            for form in self.forms:
                domain_data['forms'][form['form_name']] = {
                    'required_slots': form['required_slots']
                }
                
                # 添加表单激活动作
                domain_data['actions'].append(form['form_name'])
            
            # 添加自定义动作
            domain_data['actions'].extend([
                'action_ask_slot_validation',
                'action_handle_slot_filling',
                'action_validate_form'
            ])
            
            # 添加响应 - 避免重复
            added_responses = set()
            for instruction in self.instructions:
                # 成功响应
                success_key = f"utter_{instruction['intent']}"
                if instruction['success_response'] and success_key not in added_responses:
                    domain_data['responses'][success_key] = [
                        {'text': instruction['success_response']}
                    ]
                    added_responses.add(success_key)
                
                # 失败响应
                failure_key = f"utter_{instruction['intent']}_failure"
                if instruction['failure_response'] and failure_key not in added_responses:
                    domain_data['responses'][failure_key] = [
                        {'text': instruction['failure_response']}
                    ]
                    added_responses.add(failure_key)
                
                # 为有必需词槽的指令添加追问响应
                if instruction['has_slot_filling']:
                    for slot_name in instruction['required_slots']:
                        slot_name_en = self._generate_slot_name_en(slot_name)
                        
                        # 词槽追问响应
                        ask_response_key = f"utter_ask_{slot_name_en}"
                        if ask_response_key not in added_responses:
                            if instruction['follow_up_response']:
                                # 使用指定的追问话术，如果没有则使用默认
                                ask_text = instruction['follow_up_response'].replace('[词槽名称]', slot_name)
                            else:
                                ask_text = f"请告诉我您要设置的{slot_name}"
                            
                            domain_data['responses'][ask_response_key] = [
                                {'text': ask_text}
                            ]
                            added_responses.add(ask_response_key)
                        
                        # 词槽验证失败响应
                        validation_fail_key = f"utter_ask_{slot_name_en}_invalid"
                        if instruction['follow_up_failure_response'] and validation_fail_key not in added_responses:
                            domain_data['responses'][validation_fail_key] = [
                                {'text': instruction['follow_up_failure_response']}
                            ]
                            added_responses.add(validation_fail_key)
            
            # 添加默认响应
            domain_data['responses'].update({
                'utter_default': [
                    {'text': '抱歉，我没有理解您的意思，请您再说一遍。'}
                ],
                'utter_ask_rephrase': [
                    {'text': '请您换个说法再试一次。'}
                ],
                'utter_slot_filling_complete': [
                    {'text': '好的，我已经收集到了所有必要信息。'}
                ]
            })
            
            return yaml.dump(domain_data, allow_unicode=True, default_flow_style=False)
            
        except Exception as e:
            logger.error(f"生成Domain数据失败: {str(e)}")
            raise Exception(f"Domain数据生成错误: {str(e)}")
    
    def generate_rules_yml(self) -> str:
        """生成对话规则 - 增强版包含表单处理规则"""
        try:
            rules_data = {
                'version': '3.1',
                'rules': []
            }
            
            # 为每个有词槽填充的指令生成表单规则
            for instruction in self.instructions:
                if instruction['has_slot_filling']:
                    form_name = f"{instruction['intent']}_form"
                    
                    # 表单激活规则
                    activate_rule = {
                        'rule': f"Activate {form_name}",
                        'steps': [
                            {'intent': instruction['intent']},
                            {'action': form_name},
                            {'active_loop': form_name}
                        ]
                    }
                    rules_data['rules'].append(activate_rule)
                    
                    # 表单提交规则
                    submit_rule = {
                        'rule': f"Submit {form_name}",
                        'condition': [
                            {'active_loop': form_name}
                        ],
                        'steps': [
                            {'action': form_name},
                            {'active_loop': None},
                            {'slot_was_set': [
                                {'requested_slot': None}
                            ]},
                            {'action': f"utter_{instruction['intent']}"}
                        ]
                    }
                    rules_data['rules'].append(submit_rule)
                
                else:
                    # 简单指令规则（无需词槽填充）
                    if instruction['success_response']:
                        rule = {
                            'rule': f"Execute {instruction['intent']}",
                            'steps': [
                                {'intent': instruction['intent']},
                                {'action': f"utter_{instruction['intent']}"}
                            ]
                        }
                        rules_data['rules'].append(rule)
            
            # 添加默认fallback规则
            rules_data['rules'].append({
                'rule': 'Handle fallback',
                'steps': [
                    {'intent': 'nlu_fallback'},
                    {'action': 'utter_default'}
                ]
            })
            
            return yaml.dump(rules_data, allow_unicode=True, default_flow_style=False)
            
        except Exception as e:
            logger.error(f"生成Rules数据失败: {str(e)}")
            raise Exception(f"Rules数据生成错误: {str(e)}")
    
    def generate_stories_yml(self) -> str:
        """生成对话故事 - 增强版包含词槽填充故事"""
        try:
            stories_data = {
                'version': '3.1',
                'stories': []
            }
            
            # 为有词槽填充的指令生成复杂故事
            for instruction in self.instructions:
                if instruction['has_slot_filling']:
                    form_name = f"{instruction['intent']}_form"
                    
                    # 词槽填充成功故事
                    success_story = {
                        'story': f"{instruction['intent']} slot filling success",
                        'steps': [
                            {'intent': instruction['intent']},
                            {'action': form_name},
                            {'active_loop': form_name}
                        ]
                    }
                    
                    # 为每个必需词槽添加填充步骤
                    for slot_name in instruction['required_slots']:
                        slot_name_en = self._generate_slot_name_en(slot_name)
                        success_story['steps'].extend([
                            {'slot_was_set': [
                                {'requested_slot': slot_name_en}
                            ]},
                            {'intent': 'inform'},
                            {'action': form_name}
                        ])
                    
                    # 完成表单
                    success_story['steps'].extend([
                        {'active_loop': None},
                        {'action': f"utter_{instruction['intent']}"}
                    ])
                    
                    stories_data['stories'].append(success_story)
                    
                    # 词槽填充中断故事
                    interrupt_story = {
                        'story': f"{instruction['intent']} slot filling interrupted",
                        'steps': [
                            {'intent': instruction['intent']},
                            {'action': form_name},
                            {'active_loop': form_name},
                            {'intent': 'deny'},
                            {'action': 'utter_ask_rephrase'},
                            {'action': form_name}
                        ]
                    }
                    stories_data['stories'].append(interrupt_story)
            
            # 为每个分类生成一些基本故事
            categories = set(instruction['category'] for instruction in self.instructions)
            
            for category in categories:
                category_instructions = [inst for inst in self.instructions if inst['category'] == category and not inst['has_slot_filling']]
                
                # 简单对话故事（无词槽填充的指令）
                if category_instructions:
                    story = {
                        'story': f"{category} basic conversation",
                        'steps': [
                            {'intent': 'affirm'},
                            {'action': 'utter_default'}
                        ]
                    }
                    
                    # 添加该分类的一个指令
                    first_instruction = category_instructions[0]
                    if first_instruction['success_response']:
                        story['steps'].extend([
                            {'intent': first_instruction['intent']},
                            {'action': f"utter_{first_instruction['intent']}"}
                        ])
                    
                    stories_data['stories'].append(story)
            
            return yaml.dump(stories_data, allow_unicode=True, default_flow_style=False)
            
        except Exception as e:
            logger.error(f"生成Stories数据失败: {str(e)}")
            raise Exception(f"Stories数据生成错误: {str(e)}")
    
    def generate_actions_py(self) -> str:
        """生成自定义动作文件 - 处理追问逻辑"""
        actions_code = '''"""
自定义动作 - 处理词槽填充和追问逻辑
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict
import logging

logger = logging.getLogger(__name__)

class ActionHandleSlotFilling(Action):
    """处理词槽填充逻辑"""
    
    def name(self) -> Text:
        return "action_handle_slot_filling"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        intent_name = tracker.latest_message['intent']['name']
        active_loop = tracker.active_loop.get('name') if tracker.active_loop else None
        
        logger.info(f"处理词槽填充: intent={intent_name}, active_loop={active_loop}")
        
        # 检查是否需要激活表单
        if not active_loop and intent_name:
            form_name = f"{intent_name}_form"
            if form_name in domain.get('forms', {}):
                return [{"event": "active_loop", "name": form_name}]
        
        return []

class ActionValidateForm(FormValidationAction):
    """验证表单输入"""
    
    def name(self) -> Text:
        return "action_validate_form"
    
    def validate_fire_power(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """验证火力词槽"""
        
        valid_values = ["低火", "中火", "高火", "解冻", "中高火"]
        
        if slot_value and slot_value.lower() in [v.lower() for v in valid_values]:
            return {"fire_power": slot_value}
        else:
            dispatcher.utter_message(response="utter_ask_fire_power_invalid")
            return {"fire_power": None}
    
    def validate_dish_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """验证菜品名称词槽"""
        
        if slot_value and len(slot_value.strip()) > 0:
            return {"dish_name": slot_value}
        else:
            dispatcher.utter_message(response="utter_ask_dish_name_invalid")
            return {"dish_name": None}
    
    def validate_taste(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """验证口感词槽"""
        
        valid_values = ["脆嫩", "软烂", "嫩滑", "紧实", "脆爽", "软糯", "默认", "肉嫩味美"]
        
        if slot_value and slot_value in valid_values:
            return {"taste": slot_value}
        else:
            dispatcher.utter_message(response="utter_ask_taste_invalid")
            return {"taste": None}

class ActionAskSlotValidation(Action):
    """处理词槽验证和追问次数控制"""
    
    def name(self) -> Text:
        return "action_ask_slot_validation"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        requested_slot = tracker.get_slot("requested_slot")
        slot_attempt_count = tracker.get_slot(f"{requested_slot}_attempt_count") or 0
        
        # 追问次数控制（最多3次）
        max_attempts = 3
        
        if slot_attempt_count >= max_attempts:
            dispatcher.utter_message(
                text=f"很抱歉，我无法获取到正确的{requested_slot}信息，让我们重新开始吧。"
            )
            return [
                {"event": "active_loop", "name": None},
                {"event": "slot", "name": "requested_slot", "value": None},
                {"event": "slot", "name": f"{requested_slot}_attempt_count", "value": 0}
            ]
        
        # 增加尝试次数
        return [
            {"event": "slot", "name": f"{requested_slot}_attempt_count", "value": slot_attempt_count + 1}
        ]
'''
        
        return actions_code
    
    def convert_excel_to_rasa_yml(self, instruction_file: str, slot_file: str, output_dir: str) -> Dict[str, str]:
        """
        完整的Excel到RASA训练文件转换流程 - 增强版
        
        Args:
            instruction_file: 指令Excel文件路径
            slot_file: 词槽Excel文件路径
            output_dir: 输出目录
            
        Returns:
            Dict[str, str]: 生成的文件路径映射
        """
        try:
            logger.info("开始Excel到RASA数据转换流程（支持追问逻辑）")
            
            # 1. 处理词槽数据（必须先处理，因为指令数据依赖词槽映射）
            self.process_slot_data(slot_file)
            
            # 2. 处理指令数据
            self.process_instruction_data(instruction_file)
            
            # 3. 生成RASA文件
            nlu_content = self.generate_nlu_yml()
            domain_content = self.generate_domain_yml()
            rules_content = self.generate_rules_yml()
            stories_content = self.generate_stories_yml()
            actions_content = self.generate_actions_py()
            
            # 4. 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 5. 写入文件
            file_paths = {}
            
            files_to_write = [
                ('nlu.yml', nlu_content),
                ('domain.yml', domain_content),
                ('rules.yml', rules_content),
                ('stories.yml', stories_content),
                ('actions.py', actions_content)
            ]
            
            for filename, content in files_to_write:
                file_path = os.path.join(output_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                file_paths[filename] = file_path
                logger.info(f"已生成文件: {file_path}")
            
            # 6. 生成转换报告
            report = self.generate_conversion_report()
            report_path = os.path.join(output_dir, 'conversion_report.json')
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            file_paths['conversion_report.json'] = report_path
            
            logger.info(f"Excel到RASA数据转换完成，输出目录: {output_dir}")
            return file_paths
            
        except Exception as e:
            logger.error(f"Excel到RASA数据转换失败: {str(e)}")
            raise Exception(f"转换流程错误: {str(e)}")
    
    def generate_conversion_report(self) -> Dict[str, Any]:
        """生成转换报告 - 增强版包含追问统计"""
        slot_filling_instructions = [inst for inst in self.instructions if inst['has_slot_filling']]
        
        return {
            'conversion_time': datetime.now().isoformat(),
            'statistics': {
                'total_instructions': len(self.instructions),
                'slot_filling_instructions': len(slot_filling_instructions),
                'simple_instructions': len(self.instructions) - len(slot_filling_instructions),
                'total_slots': len(self.slots),
                'total_forms': len(self.forms),
                'instructions_by_category': self._get_instructions_by_category(),
                'slots_by_type': self._get_slots_by_type(),
                'total_training_examples': self._count_training_examples(),
                'total_entities': self._count_entities()
            },
            'instructions': [
                {
                    'intent': inst['intent'],
                    'name': inst['intent_name_cn'],
                    'category': inst['category'],
                    'has_slot_filling': inst['has_slot_filling'],
                    'required_slots': inst['required_slots'],
                    'follow_up_times': inst['follow_up_times'],
                    'training_examples_count': len(inst['training_examples'])
                }
                for inst in self.instructions
            ],
            'forms': [
                {
                    'form_name': form['form_name'],
                    'intent': form['intent'],
                    'required_slots': form['required_slots'],
                    'follow_up_times': form['follow_up_times']
                }
                for form in self.forms
            ],
            'slots': [
                {
                    'slot_name': slot['slot_name'],
                    'slot_name_en': slot['slot_name_en'],
                    'entities_count': len(slot['entities'])
                }
                for slot in self.slots
            ]
        }
    
    def _get_instructions_by_category(self) -> Dict[str, int]:
        """按分类统计指令数量"""
        category_count = {}
        for instruction in self.instructions:
            category = instruction['category']
            category_count[category] = category_count.get(category, 0) + 1
        return category_count
    
    def _get_slots_by_type(self) -> Dict[str, int]:
        """按类型统计词槽数量"""
        type_count = {}
        for slot in self.slots:
            slot_type = slot['slot_type']
            type_count[slot_type] = type_count.get(slot_type, 0) + 1
        return type_count
    
    def _count_training_examples(self) -> int:
        """统计训练样本总数"""
        total = 0
        for instruction in self.instructions:
            total += len(instruction['training_examples'])
        return total
    
    def _count_entities(self) -> int:
        """统计实体总数"""
        total = 0
        for slot in self.slots:
            total += len(slot['entities'])
        return total


# 便捷函数
def process_dual_screen_files(instruction_file: str, slot_file: str, output_dir: str) -> Dict[str, str]:
    """
    处理双屏Excel文件的便捷函数 - 增强版
    
    Args:
        instruction_file: 指令Excel文件路径
        slot_file: 词槽Excel文件路径
        output_dir: 输出目录
        
    Returns:
        Dict[str, str]: 生成的文件路径映射
    """
    processor = DualScreenProcessor()
    return processor.convert_excel_to_rasa_yml(instruction_file, slot_file, output_dir)


if __name__ == "__main__":
    # 测试代码
    instruction_file = "public/402/双屏指令-20250616导出.xlsx"
    slot_file = "public/402/双屏词槽-20250616导出.xlsx"
    output_dir = "rasa/data"
    
    try:
        result = process_dual_screen_files(instruction_file, slot_file, output_dir)
        print("转换成功！生成的文件:")
        for filename, filepath in result.items():
            print(f"  {filename}: {filepath}")
    except Exception as e:
        print(f"转换失败: {e}") 