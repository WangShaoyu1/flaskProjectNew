"""
训练数据生成服务
负责在训练开始时从数据库生成最新的RASA训练文件到版本目录
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session

from models.database_models import (
    InstructionData as DBInstructionData,
    SimilarQuestion as DBSimilarQuestion,
    SlotDefinition as DBSlotDefinition,
    SlotValue as DBSlotValue,
    InstructionLibraryMaster as DBInstructionLibraryMaster
)
from services.dual_screen_processor import DualScreenProcessor
from services.library_version_manager import LibraryVersionManager

logger = logging.getLogger(__name__)

class TrainingDataGenerator:
    """训练数据生成器 - 专门用于训练时生成版本数据"""
    
    def __init__(self):
        self.version_manager = LibraryVersionManager()
        self.processor = DualScreenProcessor()
    
    def generate_training_version_from_database(
        self, 
        db: Session, 
        library_id: int, 
        version_description: str = ""
    ) -> Tuple[str, str]:
        """
        从数据库当前状态生成新的训练版本
        
        Args:
            db: 数据库会话
            library_id: 指令库ID
            version_description: 版本描述
            
        Returns:
            Tuple[str, str]: (版本名称, 版本目录路径)
        """
        try:
            logger.info(f"🚀 [训练数据生成] 开始为指令库 {library_id} 生成训练版本")
            
            # 1. 验证指令库存在
            library = db.query(DBInstructionLibraryMaster).filter(
                DBInstructionLibraryMaster.id == library_id
            ).first()
            
            if not library:
                raise Exception(f"指令库 {library_id} 不存在")
            
            # 2. 从数据库加载最新数据
            logger.info(f"📊 [训练数据生成] 从数据库加载指令库 {library.name} 的最新数据")
            instructions_data = self._load_instructions_from_database(db, library_id)
            slots_data = self._load_slots_from_database(db, library_id)
            
            # 3. 验证数据完整性
            if not instructions_data:
                raise Exception(f"指令库 {library.name} 中没有可用的指令数据")
            
            logger.info(f"📋 [训练数据生成] 数据统计: {len(instructions_data)} 个指令, {len(slots_data)} 个词槽")
            
            # 4. 准备DualScreenProcessor
            self.processor.instructions = instructions_data
            self.processor.slots = slots_data
            
            # 重建词槽实体映射 - 使用英文名称作为键
            for slot in slots_data:
                # 同时使用中文名称和英文名称作为键，确保兼容性
                self.processor.slots_entities_map[slot['slot_name']] = slot['entities']
                self.processor.slots_entities_map[slot['slot_name_en']] = slot['entities']
            
            # 5. 生成RASA训练文件内容
            logger.info(f"📝 [训练数据生成] 生成RASA训练文件内容")
            file_contents = {
                'nlu.yml': self.processor.generate_nlu_yml(),
                'domain.yml': self.processor.generate_domain_yml(),
                'rules.yml': self.processor.generate_rules_yml(),
                'stories.yml': self.processor.generate_stories_yml()
            }
            
            # 6. 生成版本名称
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            version_name = f"v{timestamp}"
            
            if not version_description:
                version_description = f"训练时自动生成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 7. 保存到版本目录
            logger.info(f"💾 [训练数据生成] 保存版本 {version_name} 到版本目录")
            actual_version_name = self.version_manager.save_excel_generated_files(
                library_id=library_id,
                library_name=library.name,
                file_contents=file_contents,
                version_name=version_name,
                description=version_description
            )
            
            # 8. 获取版本目录路径
            version_dir = self.version_manager.library_versions_dir / f"library_{library_id}" / actual_version_name
            
            # 9. 生成训练统计报告
            stats = self._generate_training_statistics(instructions_data, slots_data)
            stats_file = version_dir / "training_statistics.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ [训练数据生成] 版本 {actual_version_name} 生成完成")
            logger.info(f"📁 [训练数据生成] 版本目录: {version_dir}")
            
            return actual_version_name, str(version_dir)
            
        except Exception as e:
            logger.error(f"❌ [训练数据生成] 生成训练版本失败: {str(e)}")
            raise Exception(f"生成训练版本失败: {str(e)}")
    
    def _load_instructions_from_database(self, db: Session, library_id: int) -> List[dict]:
        """从数据库加载指令数据"""
        logger.info(f"📖 [数据加载] 加载指令库 {library_id} 的指令数据")
        
        instructions = db.query(DBInstructionData).filter(
            DBInstructionData.library_id == library_id,
            DBInstructionData.is_enabled == True
        ).all()
        
        instructions_data = []
        for instruction in instructions:
            # 获取相似问
            similar_questions = db.query(DBSimilarQuestion).filter(
                DBSimilarQuestion.instruction_id == instruction.id,
                DBSimilarQuestion.is_enabled == True
            ).order_by(DBSimilarQuestion.sort_order).all()
            
            training_examples = []
            for sq in similar_questions:
                # 处理实体标注（如果有的话）
                training_examples.append({
                    'text': sq.question_text,
                    'entities': []  # TODO: 如果需要实体标注，在这里处理
                })
            
            # 构建指令数据
            instruction_data = {
                'intent': instruction.instruction_code,
                'intent_name_cn': instruction.instruction_name,
                'category': instruction.category or 'GENERAL',
                'description': instruction.instruction_desc or '',
                'training_examples': training_examples,
                'success_response': instruction.success_response or '',
                'failure_response': instruction.failure_response or '',
                'has_slot_filling': False,  # TODO: 根据关联词槽判断
                'required_slots': [],  # TODO: 获取关联的词槽
                'follow_up_times': 3  # 默认追问次数
            }
            
            instructions_data.append(instruction_data)
        
        logger.info(f"📊 [数据加载] 加载了 {len(instructions_data)} 个指令")
        return instructions_data
    
    def _load_slots_from_database(self, db: Session, library_id: int) -> List[dict]:
        """从数据库加载词槽数据"""
        logger.info(f"📖 [数据加载] 加载指令库 {library_id} 的词槽数据")
        
        slots = db.query(DBSlotDefinition).filter(
            DBSlotDefinition.library_id == library_id,
            DBSlotDefinition.is_active == True
        ).all()
        
        slots_data = []
        for slot in slots:
            # 获取词槽值
            slot_values = db.query(DBSlotValue).filter(
                DBSlotValue.slot_id == slot.id,
                DBSlotValue.is_active == True
            ).all()
            
            entities = []
            for sv in slot_values:
                entity = {
                    'value': sv.standard_value,
                    'synonyms': sv.aliases.split('==') if sv.aliases else []
                }
                entities.append(entity)
            
            # 生成或获取英文词槽名称
            slot_name_en = self._generate_slot_name_en(slot.slot_name)
            
            slot_data = {
                'slot_name': slot.slot_name,  # 保留中文名称用于显示
                'slot_name_en': slot_name_en,  # 英文名称用于RASA配置
                'description': slot.description or '',
                'slot_type': slot.slot_type or 'categorical',
                'entities': entities
            }
            
            slots_data.append(slot_data)
        
        logger.info(f"📊 [数据加载] 加载了 {len(slots_data)} 个词槽")
        return slots_data
    
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
    
    def _generate_training_statistics(self, instructions_data: List[dict], slots_data: List[dict]) -> Dict[str, Any]:
        """生成训练统计信息"""
        total_examples = sum(len(inst['training_examples']) for inst in instructions_data)
        total_entities = sum(len(slot['entities']) for slot in slots_data)
        
        categories = {}
        for inst in instructions_data:
            category = inst['category']
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        return {
            'generation_time': datetime.now().isoformat(),
            'data_source': 'database',
            'statistics': {
                'total_instructions': len(instructions_data),
                'total_training_examples': total_examples,
                'total_slots': len(slots_data),
                'total_entities': total_entities,
                'categories': categories
            },
            'instructions_summary': [
                {
                    'intent': inst['intent'],
                    'name': inst['intent_name_cn'],
                    'category': inst['category'],
                    'examples_count': len(inst['training_examples'])
                }
                for inst in instructions_data
            ],
            'slots_summary': [
                {
                    'slot_name': slot['slot_name'],
                    'slot_name_en': slot['slot_name_en'],
                    'entities_count': len(slot['entities'])
                }
                for slot in slots_data
            ]
        }
    
    def get_version_training_files_path(self, library_id: int, version_name: str) -> Dict[str, str]:
        """
        获取指定版本的训练文件路径
        
        Args:
            library_id: 指令库ID
            version_name: 版本名称
            
        Returns:
            Dict[str, str]: 文件名到路径的映射
        """
        version_dir = self.version_manager.library_versions_dir / f"library_{library_id}" / version_name
        
        if not version_dir.exists():
            raise Exception(f"版本目录不存在: {version_dir}")
        
        files_path = {}
        for filename in ['config.yml', 'domain.yml', 'nlu.yml', 'rules.yml', 'stories.yml']:
            file_path = version_dir / filename
            if file_path.exists():
                files_path[filename] = str(file_path)
        
        return files_path
    
    def validate_training_files(self, library_id: int, version_name: str) -> Tuple[bool, List[str]]:
        """
        验证训练文件的完整性
        
        Args:
            library_id: 指令库ID
            version_name: 版本名称
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 缺失文件列表)
        """
        try:
            files_path = self.get_version_training_files_path(library_id, version_name)
            
            required_files = ['domain.yml', 'nlu.yml']
            missing_files = []
            
            for required_file in required_files:
                if required_file not in files_path:
                    missing_files.append(required_file)
            
            return len(missing_files) == 0, missing_files
            
        except Exception as e:
            logger.error(f"验证训练文件失败: {str(e)}")
            return False, [str(e)] 