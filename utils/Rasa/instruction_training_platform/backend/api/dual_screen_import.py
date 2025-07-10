"""
双屏数据导入API
支持双屏指令和词槽Excel文件的上传和处理
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import tempfile
import shutil
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.database_models import (
    get_new_db,
    InstructionLibraryMaster as DBInstructionLibraryMaster,
    InstructionData as DBInstructionData,
    SimilarQuestion as DBSimilarQuestion,
    SlotDefinition as DBSlotDefinition,
    SlotValue as DBSlotValue
)
from services.dual_screen_processor import DualScreenProcessor
from response_utils import StandardResponse, success_response, error_response, ErrorCodes, Messages

router = APIRouter(prefix="/api/v2/dual-screen", tags=["双屏数据导入"])

@router.post("/upload-and-process")
async def upload_and_process_dual_screen_files(
    library_id: int = Form(..., description="指令库ID"),
    instruction_file: UploadFile = File(..., description="双屏指令Excel文件"),
    slot_file: UploadFile = File(..., description="双屏词槽Excel文件"),
    db: Session = Depends(get_new_db)
):
    """
    上传并处理双屏指令和词槽Excel文件
    
    Args:
        library_id: 目标指令库ID
        instruction_file: 双屏指令Excel文件
        slot_file: 双屏词槽Excel文件
        db: 数据库会话
        
    Returns:
        Dict: 处理结果
    """
    temp_dir = None
    
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 验证文件格式
        if not instruction_file.filename.endswith(('.xlsx', '.xls')):
            return error_response(msg="指令文件必须是Excel格式", code=ErrorCodes.PARAM_ERROR)
        
        if not slot_file.filename.endswith(('.xlsx', '.xls')):
            return error_response(msg="词槽文件必须是Excel格式", code=ErrorCodes.PARAM_ERROR)
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        # 保存上传的文件
        instruction_path = os.path.join(temp_dir, instruction_file.filename)
        slot_path = os.path.join(temp_dir, slot_file.filename)
        
        with open(instruction_path, "wb") as buffer:
            shutil.copyfileobj(instruction_file.file, buffer)
        
        with open(slot_path, "wb") as buffer:
            shutil.copyfileobj(slot_file.file, buffer)
        
        # 处理Excel文件
        processor = DualScreenProcessor()
        
        # 先处理词槽数据
        slots_data = processor.process_slot_data(slot_path)
        
        # 再处理指令数据
        instructions_data = processor.process_instruction_data(instruction_path)
        
        # 保存到数据库
        import_result = await _save_to_database(
            db, library_id, instructions_data, slots_data
        )
        
        # 生成RASA训练文件（可选）
        rasa_output_dir = f"rasa/data/library_{library_id}"
        rasa_files = processor.convert_excel_to_rasa_yml(
            instruction_path, slot_path, rasa_output_dir
        )
        
        return success_response(data={"success": True,
            "message": "双屏数据导入成功",
            "library_id": library_id,
            "library_name": library.name,
            "import_statistics": import_result,
            "rasa_files": rasa_files,
            "processing_time": datetime.now().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        return error_response(msg="处理失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)
    
    finally:
        # 清理临时文件
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@router.post("/generate-rasa-files/{library_id}")
async def generate_rasa_files_from_database(
    library_id: int,
    db: Session = Depends(get_new_db)
):
    """
    从数据库数据生成RASA训练文件
    
    Args:
        library_id: 指令库ID
        db: 数据库会话
        
    Returns:
        Dict: 生成结果
    """
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 从数据库加载数据
        instructions_data = _load_instructions_from_database(db, library_id)
        slots_data = _load_slots_from_database(db, library_id)
        
        if not instructions_data:
            return error_response(msg="指令库中没有指令数据", code=ErrorCodes.PARAM_ERROR)
        
        # 生成RASA文件
        processor = DualScreenProcessor()
        processor.instructions = instructions_data
        processor.slots = slots_data
        
        # 重建词槽实体映射
        for slot in slots_data:
            processor.slots_entities_map[slot['slot_name']] = slot['entities']
        
        # 生成训练文件
        rasa_output_dir = f"rasa/data/library_{library_id}"
        
        nlu_content = processor.generate_nlu_yml()
        domain_content = processor.generate_domain_yml()
        rules_content = processor.generate_rules_yml()
        stories_content = processor.generate_stories_yml()
        
        # 保存文件
        os.makedirs(rasa_output_dir, exist_ok=True)
        
        files_written = {}
        for filename, content in [
            ('nlu.yml', nlu_content),
            ('domain.yml', domain_content),
            ('rules.yml', rules_content),
            ('stories.yml', stories_content)
        ]:
            file_path = os.path.join(rasa_output_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            files_written[filename] = file_path
        
        return success_response(data={"success": True,
            "message": "RASA训练文件生成成功",
            "library_id": library_id,
            "library_name": library.name,
            "files": files_written,
            "output_directory": rasa_output_dir
        })
        
    except HTTPException:
        raise
    except Exception as e:
        return error_response(msg="生成失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)

async def _save_to_database(
    db: Session, 
    library_id: int, 
    instructions_data: List[dict], 
    slots_data: List[dict]
) -> dict:
    """保存处理后的数据到数据库"""
    
    try:
        # 统计信息
        stats = {
            "instructions_imported": 0,
            "similar_questions_imported": 0,
            "slots_imported": 0,
            "slot_values_imported": 0
        }
        
        # 保存词槽数据
        for slot_data in slots_data:
            # 检查词槽是否已存在
            existing_slot = db.query(DBSlotDefinition).filter(
                DBSlotDefinition.library_id == library_id,
                DBSlotDefinition.slot_name == slot_data['slot_name']
            ).first()
            
            if existing_slot:
                # 更新现有词槽
                existing_slot.slot_name_en = slot_data['slot_name_en']
                existing_slot.description = slot_data['description']
                existing_slot.slot_type = slot_data['slot_type']
                slot_record = existing_slot
                
                # 删除旧的词槽值
                db.query(DBSlotValue).filter(
                    DBSlotValue.slot_id == existing_slot.id
                ).delete()
            else:
                # 创建新词槽
                slot_record = DBSlotDefinition(
                    library_id=library_id,
                    slot_name=slot_data['slot_name'],
                    slot_name_en=slot_data['slot_name_en'],
                    description=slot_data['description'],
                    slot_type=slot_data['slot_type'],
                    is_required=False,
                    is_active=True
                )
                db.add(slot_record)
                db.flush()
                stats["slots_imported"] += 1
            
            # 保存词槽值
            for entity in slot_data['entities']:
                slot_value = DBSlotValue(
                    slot_id=slot_record.id,
                    standard_value=entity['value'],
                    aliases='=='.join(entity['synonyms']) if entity['synonyms'] else '',
                    is_active=True
                )
                db.add(slot_value)
                stats["slot_values_imported"] += 1
        
        # 保存指令数据
        for instruction_data in instructions_data:
            # 检查指令是否已存在
            existing_instruction = db.query(DBInstructionData).filter(
                DBInstructionData.library_id == library_id,
                DBInstructionData.instruction_code == instruction_data['intent']
            ).first()
            
            if existing_instruction:
                # 更新现有指令
                existing_instruction.instruction_name = instruction_data['intent_name_cn']
                existing_instruction.instruction_desc = instruction_data['description']
                existing_instruction.category = instruction_data['category']
                existing_instruction.success_response = instruction_data['success_response']
                existing_instruction.failure_response = instruction_data['failure_response']
                instruction_record = existing_instruction
                
                # 删除旧的相似问
                db.query(DBSimilarQuestion).filter(
                    DBSimilarQuestion.instruction_id == existing_instruction.id
                ).delete()
            else:
                # 创建新指令
                instruction_record = DBInstructionData(
                    library_id=library_id,
                    instruction_name=instruction_data['intent_name_cn'],
                    instruction_code=instruction_data['intent'],
                    instruction_desc=instruction_data['description'],
                    category=instruction_data['category'],
                    success_response=instruction_data['success_response'],
                    failure_response=instruction_data['failure_response'],
                    is_enabled=True
                )
                db.add(instruction_record)
                db.flush()
                stats["instructions_imported"] += 1
            
            # 保存相似问（从训练样本中提取）
            for i, example in enumerate(instruction_data['training_examples']):
                similar_question = DBSimilarQuestion(
                    instruction_id=instruction_record.id,
                    question_text=example['text'],
                    is_enabled=True,
                    sort_order=i + 1
                )
                db.add(similar_question)
                stats["similar_questions_imported"] += 1
        
        db.commit()
        return success_response(data=stats)
    except Exception as e:
        db.rollback()
        raise Exception(f"数据库保存失败: {str(e)}")

def _load_instructions_from_database(db: Session, library_id: int) -> List[dict]:
    """从数据库加载指令数据"""
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
        ).all()
        
        training_examples = [
            {'text': sq.question_text, 'entities': []}
            for sq in similar_questions
        ]
        
        instructions_data.append({
            'intent': instruction.instruction_code,
            'intent_name_cn': instruction.instruction_name,
            'category': instruction.category or '',
            'description': instruction.instruction_desc or '',
            'training_examples': training_examples,
            'success_response': instruction.success_response or '',
            'failure_response': instruction.failure_response or ''
        })
    
    return instructions_data

def _load_slots_from_database(db: Session, library_id: int) -> List[dict]:
    """从数据库加载词槽数据"""
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
        
        slots_data.append({
            'slot_name': slot.slot_name,
            'slot_name_en': slot.slot_name_en,
            'description': slot.description or '',
            'slot_type': slot.slot_type,
            'entities': entities
        })
    
    return slots_data