#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能对话训练平台 - 新数据库初始化脚�?用于创建全新的数据库表结构和初始化数�?"""

import sys
import os
from datetime import datetime

# 添加backend路径到sys.path
sys.path.append(os.path.dirname(__file__))

from models.database_models import (
    Base, new_engine, NewSessionLocal, create_new_tables,
    InstructionLibraryMaster, InstructionData, SimilarQuestion,
    SlotDefinition, SlotValue, ModelTrainingRecord,
    InstructionTestRecord, TestDetail, SystemConfig
)


def init_new_database():
    """初始化新数据�?""
    print("🚀 开始初始化智能对话训练平台数据�?..")
    
    try:
        # 创建所有表
        print("📋 创建数据库表结构...")
        create_new_tables()
        print("�?数据库表创建成功")
        
        # 初始化系统配�?        print("⚙️ 初始化系统配�?..")
        init_system_config()
        print("�?系统配置初始化完�?)
        
        # 创建示例数据
        print("📝 创建示例数据...")
        create_sample_data()
        print("�?示例数据创建完成")
        
        print("🎉 新数据库初始化完成！")
        
    except Exception as e:
        print(f"�?初始化失�? {e}")
        raise


def init_system_config():
    """初始化系统配�?""
    db = NewSessionLocal()
    
    try:
        # 基础系统配置
        configs = [
            {
                'config_key': 'system.version',
                'config_value': '1.0.0',
                'config_desc': '系统版本�?
            },
            {
                'config_key': 'rasa.default_language',
                'config_value': 'zh-CN',
                'config_desc': 'RASA默认语言'
            },
            {
                'config_key': 'training.default_epochs',
                'config_value': '100',
                'config_desc': '默认训练轮数'
            },
            {
                'config_key': 'training.confidence_threshold',
                'config_value': '0.8',
                'config_desc': '默认置信度阈�?
            },
            {
                'config_key': 'file.max_upload_size',
                'config_value': '10485760',  # 10MB
                'config_desc': '文件上传大小限制(字节)'
            },
            {
                'config_key': 'model.max_versions',
                'config_value': '10',
                'config_desc': '模型版本保留数量上限'
            }
        ]
        
        for config_data in configs:
            config = SystemConfig(**config_data)
            db.add(config)
        
        db.commit()
        print(f"   �?已创�?{len(configs)} 个系统配置项")
        
    except Exception as e:
        db.rollback()
        print(f"   �?系统配置初始化失�? {e}")
        raise
    finally:
        db.close()


def create_sample_data():
    """创建示例数据"""
    db = NewSessionLocal()
    
    try:
        # 创建示例指令�?        sample_library = InstructionLibraryMaster(
            name="智能家居控制指令�?,
            language="zh-CN",
            description="用于智能家居设备控制的对话指令库",
            business_code="SMART_HOME_001",
            created_by="system"
        )
        db.add(sample_library)
        db.flush()  # 获取ID
        
        # 创建示例词槽
        room_slot = SlotDefinition(
            library_id=sample_library.id,
            slot_name="房间名称",
            slot_name_en="room_name",
            slot_type="categorical",
            description="房间位置词槽",
            is_required=False,
            is_active=True
        )
        db.add(room_slot)
        db.flush()
        
        # 创建词槽�?        room_values = [
            {
                'standard_value': '客厅',
                'aliases': '大厅==会客�?=起居�?,
                'description': '客厅房间'
            },
            {
                'standard_value': '卧室',
                'aliases': '主卧==次卧==睡房',
                'description': '卧室房间'
            },
            {
                'standard_value': '厨房',
                'aliases': '灶台==下厨�?,
                'description': '厨房区域'
            }
        ]
        
        for i, value_data in enumerate(room_values):
            slot_value = SlotValue(
                slot_id=room_slot.id,
                sort_order=i + 1,
                **value_data
            )
            db.add(slot_value)
        
        # 创建示例指令数据
        sample_instructions = [
            {
                'instruction_name': '开灯指�?,
                'instruction_code': 'LIGHT_ON',
                'instruction_desc': '打开指定房间的灯�?,
                'category': '照明控制',
                'is_slot_related': True,
                'related_slot_ids': f'[{room_slot.id}]',
                'success_response': '已为您打开{room_name}的灯�?,
                'failure_response': '抱歉，无法打开{room_name}的灯光，请检查设备连�?,
                'similar_questions': ['打开客厅的灯', '开�?, '点亮客厅', '客厅开�?]
            },
            {
                'instruction_name': '关灯指令',
                'instruction_code': 'LIGHT_OFF',
                'instruction_desc': '关闭指定房间的灯�?,
                'category': '照明控制',
                'is_slot_related': True,
                'related_slot_ids': f'[{room_slot.id}]',
                'success_response': '已为您关闭{room_name}的灯�?,
                'failure_response': '抱歉，无法关闭{room_name}的灯光，请检查设备连�?,
                'similar_questions': ['关闭客厅的灯', '关灯', '熄灭客厅�?, '客厅关灯']
            },
            {
                'instruction_name': '查询天气',
                'instruction_code': 'WEATHER_QUERY',
                'instruction_desc': '查询当前天气信息',
                'category': '信息查询',
                'is_slot_related': False,
                'related_slot_ids': None,
                'success_response': '今天天气晴朗，温度适宜',
                'failure_response': '抱歉，暂时无法获取天气信�?,
                'similar_questions': ['今天天气怎么�?, '查询天气', '天气预报', '现在什么天�?]
            }
        ]
        
        for i, instruction_data in enumerate(sample_instructions):
            similar_questions = instruction_data.pop('similar_questions')
            
            instruction = InstructionData(
                library_id=sample_library.id,
                sort_order=i + 1,
                **instruction_data
            )
            db.add(instruction)
            db.flush()
            
            # 添加相似�?            for j, question_text in enumerate(similar_questions):
                similar_question = SimilarQuestion(
                    instruction_id=instruction.id,
                    question_text=question_text,
                    sort_order=j + 1
                )
                db.add(similar_question)
        
        db.commit()
        print(f"   �?已创建示例指令库: {sample_library.name}")
        print(f"   �?已创�?{len(sample_instructions)} 个示例指�?)
        print(f"   �?已创�?1 个词槽，{len(room_values)} 个词槽�?)
        
    except Exception as e:
        db.rollback()
        print(f"   �?示例数据创建失败: {e}")
        raise
    finally:
        db.close()


def verify_database():
    """验证数据库创建结�?""
    print("\n🔍 验证数据库创建结�?..")
    
    db = NewSessionLocal()
    try:
        # 检查表是否存在
        tables_to_check = [
            (InstructionLibraryMaster, "指令库母版表"),
            (InstructionData, "指令数据�?),
            (SimilarQuestion, "相似问表"),
            (SlotDefinition, "词槽定义�?),
            (SlotValue, "词槽值表"),
            (ModelTrainingRecord, "模型训练记录�?),
            (InstructionTestRecord, "指令测试记录�?),
            (TestDetail, "测试详情�?),
            (SystemConfig, "系统配置�?)
        ]
        
        for model_class, table_name in tables_to_check:
            count = db.query(model_class).count()
            print(f"   �?{table_name}: {count} 条记�?)
        
        print("�?数据库验证完�?)
        
    except Exception as e:
        print(f"�?数据库验证失�? {e}")
        raise
    finally:
        db.close()


def main():
    """主函�?""
    print("=" * 60)
    print("智能对话训练平台 - 数据库初始化")
    print("=" * 60)
    print(f"初始化时�? {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化数据库
    init_new_database()
    
    # 验证结果
    verify_database()
    
    print("\n🎉 数据库初始化完成！系统已准备就绪�?)
    print("📋 下一步可以：")
    print("   1. 启动后端服务")
    print("   2. 开始创建指令库")
    print("   3. 录入训练数据")


if __name__ == '__main__':
    main() 
