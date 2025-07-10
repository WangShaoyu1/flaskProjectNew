#!/usr/bin/env python3
"""创建model_training.py文件的脚本"""

content = '''"""
模型训练API - 简化版本
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime

from models.database_models import (
    get_new_db,
    InstructionLibraryMaster, 
    ModelTrainingRecord
)
from models.schemas import TrainingStatus, StandardResponse
from response_utils import success_response, error_response, ErrorCodes

router = APIRouter(prefix="/api/v2/training", tags=["模型训练"])

# 简化的训练接口
@router.get("/records")
async def get_training_records(
    library_id: int = Query(..., description="指令库ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_new_db)
):
    """获取训练记录列表"""
    try:
        # 验证指令库是否存在
        library = db.query(InstructionLibraryMaster).filter(
            InstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 获取训练记录
        records = db.query(ModelTrainingRecord).filter(
            ModelTrainingRecord.library_id == library_id
        ).order_by(
            ModelTrainingRecord.version_number.desc()
        ).offset(skip).limit(limit).all()
        
        total = db.query(ModelTrainingRecord).filter(
            ModelTrainingRecord.library_id == library_id
        ).count()
        
        return success_response(data={
            "records": records,
            "total": total,
            "library_id": library_id,
            "library_name": library.name
        })
        
    except HTTPException:
        raise
    except Exception as e:
        return error_response(msg=f"获取训练记录失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


@router.get("/library/{library_id}/summary")
async def get_training_summary(
    library_id: int,
    db: Session = Depends(get_new_db)
):
    """获取指令库的训练汇总信息"""
    try:
        # 验证指令库是否存在
        library = db.query(InstructionLibraryMaster).filter(
            InstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 获取训练统计
        total_trainings = db.query(ModelTrainingRecord).filter(
            ModelTrainingRecord.library_id == library_id
        ).count()
        
        successful_trainings = db.query(ModelTrainingRecord).filter(
            ModelTrainingRecord.library_id == library_id,
            ModelTrainingRecord.training_status == TrainingStatus.SUCCESS
        ).count()
        
        return success_response(data={
            "library_id": library_id,
            "library_name": library.name,
            "total_trainings": total_trainings,
            "successful_trainings": successful_trainings,
            "success_rate": (successful_trainings / total_trainings * 100) if total_trainings > 0 else 0
        })
        
    except HTTPException:
        raise
    except Exception as e:
        return error_response(msg=f"获取训练汇总失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)
'''

# 写入文件
with open('backend/api/model_training.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("model_training.py 文件创建成功") 