# 智能对话训练平台 - 指令库母版管理API
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.database_models import (
    get_new_db, InstructionLibraryMaster as DBInstructionLibraryMaster,
    InstructionData as DBInstructionData, SlotDefinition as DBSlotDefinition,
    ModelTrainingRecord as DBModelTrainingRecord
)
from models.schemas import (
    InstructionLibraryMaster, InstructionLibraryMasterCreate,
    ApiResponse
)
from response_utils import StandardResponse, success_response, error_response, ErrorCodes, Messages
from utils.logger import log_database, log_error

router = APIRouter(prefix="/api/v2/library", tags=["指令库母版管理"])

@router.get("/list", response_model=StandardResponse)
async def get_library_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_new_db)
):
    """获取指令库列表"""
    try:
        query = db.query(DBInstructionLibraryMaster)
        
        if is_active is not None:
            query = query.filter(DBInstructionLibraryMaster.is_active == is_active)
        
        libraries = query.offset(skip).limit(limit).all()
        
        # 为每个库添加统计信息
        result = []
        for library in libraries:
            library_dict = {
                "id": library.id,
                "name": library.name,
                "language": library.language,
                "description": library.description,
                "business_code": library.business_code,
                "created_by": library.created_by,
                "created_time": library.created_time,
                "updated_time": library.updated_time,
                "is_active": library.is_active,
                "instruction_count": db.query(DBInstructionData).filter(
                    DBInstructionData.library_id == library.id
                ).count(),
                "slot_count": db.query(DBSlotDefinition).filter(
                    DBSlotDefinition.library_id == library.id
                ).count(),
                "latest_version": None
            }
            
            # 获取最新训练版本
            latest_training = db.query(DBModelTrainingRecord).filter(
                DBModelTrainingRecord.library_id == library.id
            ).order_by(DBModelTrainingRecord.version_number.desc()).first()
            
            if latest_training:
                library_dict["latest_version"] = latest_training.version_number
            
            result.append(library_dict)
        
        return success_response(data=result, msg="获取指令库列表成功")
        
    except Exception as e:
        return error_response(msg=f"获取指令库列表失败: {str(e)}", code=ErrorCodes.DATABASE_ERROR)

@router.post("/create", response_model=StandardResponse)
async def create_library(
    library_data: InstructionLibraryMasterCreate,
    db: Session = Depends(get_new_db)
):
    """创建新的指令库"""
    try:
        # 检查名称是否重复
        existing = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.name == library_data.name
        ).first()
        
        if existing:
            return error_response(msg="指令库名称已存在", code=ErrorCodes.ALREADY_EXISTS)
        
        # 创建新指令库
        new_library = DBInstructionLibraryMaster(**library_data.dict())
        db.add(new_library)
        db.commit()
        db.refresh(new_library)
        
        # 记录数据库操作日志
        log_database(
            operation="CREATE",
            table="instruction_library_master",
            record_id=new_library.id,
            extra_data={
                "library_name": new_library.name,
                "created_by": new_library.created_by,
                "business_code": new_library.business_code
            }
        )
        
        return success_response(
            data={"library_id": new_library.id},
            msg=f"指令库'{library_data.name}' 创建成功"
        )
        
    except Exception as e:
        db.rollback()
        return error_response(msg=f"创建指令库失败: {str(e)}", code=ErrorCodes.DATABASE_ERROR)

@router.get("/{library_id}", response_model=StandardResponse)
async def get_library_detail(
    library_id: int,
    db: Session = Depends(get_new_db)
):
    """获取指令库详情"""
    try:
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 构建详情信息
        library_dict = {
            "id": library.id,
            "name": library.name,
            "language": library.language,
            "description": library.description,
            "business_code": library.business_code,
            "created_by": library.created_by,
            "created_time": library.created_time,
            "updated_time": library.updated_time,
            "is_active": library.is_active,
            "instruction_count": db.query(DBInstructionData).filter(
                DBInstructionData.library_id == library_id
            ).count(),
            "slot_count": db.query(DBSlotDefinition).filter(
                DBSlotDefinition.library_id == library_id
            ).count(),
            "latest_version": None
        }
        
        # 获取最新训练版本
        latest_training = db.query(DBModelTrainingRecord).filter(
            DBModelTrainingRecord.library_id == library_id
        ).order_by(DBModelTrainingRecord.version_number.desc()).first()
        
        if latest_training:
            library_dict["latest_version"] = latest_training.version_number
        
        return success_response(data=library_dict, msg="获取指令库详情成功")
        
    except Exception as e:
        return error_response(msg=f"获取指令库详情失败: {str(e)}", code=ErrorCodes.DATABASE_ERROR)

@router.put("/{library_id}", response_model=StandardResponse)
async def update_library(
    library_id: int,
    library_data: InstructionLibraryMasterCreate,
    db: Session = Depends(get_new_db)
):
    """更新指令库"""
    try:
        # 查找指令库
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 检查名称是否重复（排除当前库）
        existing = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.name == library_data.name,
            DBInstructionLibraryMaster.id != library_id
        ).first()
        
        if existing:
            return error_response(msg="指令库名称已存在", code=ErrorCodes.ALREADY_EXISTS)
        
        # 更新字段
        for field, value in library_data.dict(exclude_unset=True).items():
            setattr(library, field, value)
        
        db.commit()
        db.refresh(library)
        
        # 记录数据库操作日志
        log_database(
            operation="UPDATE",
            table="instruction_library_master",
            record_id=library.id,
            extra_data={
                "library_name": library.name,
                "updated_fields": list(library_data.dict(exclude_unset=True).keys())
            }
        )
        
        return success_response(
            data={"library_id": library.id},
            msg=f"指令库'{library.name}' 更新成功"
        )
        
    except Exception as e:
        db.rollback()
        return error_response(msg=f"更新指令库失败: {str(e)}", code=ErrorCodes.DATABASE_ERROR)

@router.delete("/{library_id}", response_model=StandardResponse)
async def delete_library(
    library_id: int,
    db: Session = Depends(get_new_db)
):
    """删除指令库"""
    try:
        # 查找指令库
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 检查是否有关联数据
        instruction_count = db.query(DBInstructionData).filter(
            DBInstructionData.library_id == library_id
        ).count()
        
        slot_count = db.query(DBSlotDefinition).filter(
            DBSlotDefinition.library_id == library_id
        ).count()
        
        training_count = db.query(DBModelTrainingRecord).filter(
            DBModelTrainingRecord.library_id == library_id
        ).count()
        
        if instruction_count > 0 or slot_count > 0 or training_count > 0:
            return error_response(
                msg=f"指令库包含数据，无法删除。指令: {instruction_count}个，词槽: {slot_count}个，训练记录: {training_count}个",
                code=ErrorCodes.VALIDATION_ERROR
            )
        
        # 删除指令库
        library_name = library.name
        db.delete(library)
        db.commit()
        
        # 记录数据库操作日志
        log_database(
            operation="DELETE",
            table="instruction_library_master",
            record_id=library_id,
            extra_data={
                "library_name": library_name,
                "deleted_by": "system"  # 可以从请求中获取用户信息
            }
        )
        
        return success_response(
            data={"library_id": library_id},
            msg=f"指令库'{library_name}' 删除成功"
        )
        
    except Exception as e:
        db.rollback()
        return error_response(msg=f"删除指令库失败: {str(e)}", code=ErrorCodes.DATABASE_ERROR)

@router.get("/{library_id}/stats", response_model=StandardResponse)
async def get_library_stats(
    library_id: int,
    db: Session = Depends(get_new_db)
):
    """获取指令库统计信息"""
    try:
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 获取统计信息
        stats = {
            "library_id": library_id,
            "library_name": library.name,
            "instruction_count": db.query(DBInstructionData).filter(
                DBInstructionData.library_id == library_id
            ).count(),
            "slot_count": db.query(DBSlotDefinition).filter(
                DBSlotDefinition.library_id == library_id
            ).count(),
            "training_count": db.query(DBModelTrainingRecord).filter(
                DBModelTrainingRecord.library_id == library_id
            ).count()
        }
        
        return success_response(data=stats, msg="获取统计信息成功")
        
    except Exception as e:
        return error_response(msg=f"获取统计信息失败: {str(e)}", code=ErrorCodes.DATABASE_ERROR) 



