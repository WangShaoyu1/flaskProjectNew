#!/usr/bin/env python3
"""
检查数据库中的实际数据
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# 设置正确的数据库路径
os.environ['DATABASE_URL'] = 'sqlite:///./backend/database/instruction_platform_new.db'

from database import get_db
from models.database_models import InstructionData, SlotDefinition, InstructionLibraryMaster

def check_database():
    """检查数据库数据"""
    try:
        db = next(get_db())
        
        # 检查指令库
        libraries = db.query(InstructionLibraryMaster).all()
        print(f'📚 指令库数量: {len(libraries)}')
        for lib in libraries:
            print(f'  ID: {lib.id}, 名称: {lib.name}')
        
        # 检查指令数据
        instructions = db.query(InstructionData).all()
        print(f'📝 指令数量: {len(instructions)}')
        
        # 按库ID分组统计
        library_instruction_count = {}
        for inst in instructions:
            lib_id = inst.library_id
            if lib_id not in library_instruction_count:
                library_instruction_count[lib_id] = 0
            library_instruction_count[lib_id] += 1
        
        print(f'📊 按库ID统计指令数量:')
        for lib_id, count in library_instruction_count.items():
            print(f'  库ID {lib_id}: {count} 条指令')
        
        # 显示前3条指令
        if instructions:
            print(f'📋 前3条指令:')
            for inst in instructions[:3]:
                print(f'  ID: {inst.id}, 库ID: {inst.library_id}, 指令: {inst.instruction_name}')
        
        # 检查词槽数据
        slots = db.query(SlotDefinition).all()
        print(f'🔧 词槽数量: {len(slots)}')
        
        # 按库ID分组统计
        library_slot_count = {}
        for slot in slots:
            lib_id = slot.library_id
            if lib_id not in library_slot_count:
                library_slot_count[lib_id] = 0
            library_slot_count[lib_id] += 1
        
        print(f'📊 按库ID统计词槽数量:')
        for lib_id, count in library_slot_count.items():
            print(f'  库ID {lib_id}: {count} 个词槽')
        
        # 显示前3个词槽
        if slots:
            print(f'📋 前3个词槽:')
            for slot in slots[:3]:
                print(f'  ID: {slot.id}, 库ID: {slot.library_id}, 名称: {slot.slot_name}')
        
        # 检查相似问（训练样本）
        from models.database_models import SimilarQuestion
        similar_questions = db.query(SimilarQuestion).all()
        print(f'🎯 相似问（训练样本）统计:')
        print(f'  总数量: {len(similar_questions)}')
        
        # 按指令ID分组统计
        instruction_sample_count = {}
        for sq in similar_questions:
            inst_id = sq.instruction_id
            if inst_id not in instruction_sample_count:
                instruction_sample_count[inst_id] = 0
            instruction_sample_count[inst_id] += 1
        
        print(f'  按指令统计样本数量:')
        for inst_id, count in list(instruction_sample_count.items())[:5]:
            instruction = db.query(InstructionData).filter(InstructionData.id == inst_id).first()
            if instruction:
                print(f'    指令 {inst_id} ({instruction.instruction_name}): {count} 个样本')
        
        db.close()
        
    except Exception as e:
        print(f'❌ 检查数据库失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database() 