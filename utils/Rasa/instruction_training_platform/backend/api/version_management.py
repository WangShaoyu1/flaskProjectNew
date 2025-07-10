#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
版本管理API模块
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from models.database_models import get_new_db, ModelTrainingRecord, InstructionLibraryMaster
from utils.response_utils import success_response, error_response, ErrorCodes

router = APIRouter(prefix="/api/v2/version", tags=["版本管理"])

@router.get("/list")
async def get_version_list(
    library_id: Optional[int] = None,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_new_db)
):
    """获取版本列表"""
    try:
        query = db.query(ModelTrainingRecord)
        if library_id:
            query = query.filter(ModelTrainingRecord.library_id == library_id)
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * size
        versions = query.order_by(ModelTrainingRecord.version_number.desc()).offset(offset).limit(size).all()
        
        version_list = []
        for version in versions:
            version_list.append({
                "id": version.id,
                "version_number": version.version_number,
                "training_status": version.training_status,
                "start_time": version.start_time.isoformat() if version.start_time else None,
                "complete_time": version.complete_time.isoformat() if version.complete_time else None,
                "intent_count": version.intent_count,
                "is_active": version.is_active,
                "library_id": version.library_id
            })
        
        # 返回分页数据
        result = {
            "items": version_list,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
        
        return success_response(data=result, msg="获取版本列表成功")
    
    except Exception as e:
        return error_response(msg=f"获取版本列表失败: {str(e)}", code=ErrorCodes.DATABASE_ERROR)

@router.get("/active/{library_id}")
async def get_active_version(
    library_id: int,
    db: Session = Depends(get_new_db)
):
    """获取指定指令库的当前激活版本"""
    try:
        # 查找激活的版本
        active_version = db.query(ModelTrainingRecord).filter(
            ModelTrainingRecord.library_id == library_id,
            ModelTrainingRecord.is_active == True
        ).first()
        
        if not active_version:
            return success_response(data=None, msg="该指令库暂无激活版本")
        
        version_data = {
            "id": active_version.id,
            "version_number": active_version.version_number,
            "training_status": active_version.training_status,
            "start_time": active_version.start_time.isoformat() if active_version.start_time else None,
            "complete_time": active_version.complete_time.isoformat() if active_version.complete_time else None,
            "intent_count": active_version.intent_count,
            "slot_count": active_version.slot_count,
            "training_data_count": active_version.training_data_count,
            "is_active": active_version.is_active,
            "library_id": active_version.library_id
        }
        
        return success_response(data=version_data, msg="获取激活版本成功")
    
    except Exception as e:
        return error_response(msg=f"获取激活版本失败: {str(e)}", code=ErrorCodes.DATABASE_ERROR)

@router.post("/activate/{version_id}")
async def activate_version(
    version_id: int,
    db: Session = Depends(get_new_db)
):
    """激活指定版本"""
    try:
        # 获取目标版本
        target_version = db.query(ModelTrainingRecord).filter(
            ModelTrainingRecord.id == version_id
        ).first()
        
        if not target_version:
            return error_response(msg="版本不存在", code=ErrorCodes.NOT_FOUND)
        
        # 停用当前激活的版本
        db.query(ModelTrainingRecord).filter(
            ModelTrainingRecord.library_id == target_version.library_id,
            ModelTrainingRecord.is_active == True
        ).update({"is_active": False})
        
        # 激活目标版本
        target_version.is_active = True
        
        db.commit()
        
        return success_response(msg="版本激活成功")
    
    except Exception as e:
        db.rollback()
        return error_response(msg=f"版本激活失败: {str(e)}", code=ErrorCodes.DATABASE_ERROR)

@router.get("/detail/{version_id}")
async def get_version_details(
    version_id: int,
    db: Session = Depends(get_new_db)
):
    """获取版本详情"""
    try:
        version = db.query(ModelTrainingRecord).filter(
            ModelTrainingRecord.id == version_id
        ).first()
        
        if not version:
            return error_response(msg="版本不存在", code=ErrorCodes.NOT_FOUND)
        
        details = {
            "id": version.id,
            "version_number": version.version_number,
            "training_status": version.training_status,
            "start_time": version.start_time.isoformat() if version.start_time else None,
            "complete_time": version.complete_time.isoformat() if version.complete_time else None,
            "intent_count": version.intent_count,
            "slot_count": version.slot_count,
            "training_data_count": version.training_data_count,
            "is_active": version.is_active,
            "model_file_path": version.model_file_path,
            "training_log": version.training_log,
            "error_message": version.error_message,
            "library_id": version.library_id
        }
        
        return success_response(data=details, msg="获取版本详情成功")
    
    except Exception as e:
        return error_response(msg=f"获取版本详情失败: {str(e)}", code=ErrorCodes.DATABASE_ERROR)

@router.delete("/{version_id}")
async def delete_version(
    version_id: int,
    force: bool = False,
    db: Session = Depends(get_new_db)
):
    """删除版本"""
    try:
        version = db.query(ModelTrainingRecord).filter(
            ModelTrainingRecord.id == version_id
        ).first()
        
        if not version:
            return error_response(msg="版本不存在", code=ErrorCodes.NOT_FOUND)
        
        if version.is_active and not force:
            return error_response(msg="不能删除激活的版本", code=ErrorCodes.BUSINESS_ERROR)
        
        db.delete(version)
        db.commit()
        
        return success_response(msg="版本删除成功")
    
    except Exception as e:
        db.rollback()
        return error_response(msg=f"版本删除失败: {str(e)}", code=ErrorCodes.DATABASE_ERROR)

@router.post("/compare")
async def compare_versions(
    data: dict,
    db: Session = Depends(get_new_db)
):
    """版本对比"""
    try:
        version_id_1 = data.get("version_id_1")
        version_id_2 = data.get("version_id_2")
        
        if not version_id_1 or not version_id_2:
            return error_response(msg="请提供两个版本ID", code=ErrorCodes.VALIDATION_ERROR)
        
        # 获取两个版本的信息
        version_1 = db.query(ModelTrainingRecord).filter(
            ModelTrainingRecord.id == version_id_1
        ).first()
        
        version_2 = db.query(ModelTrainingRecord).filter(
            ModelTrainingRecord.id == version_id_2
        ).first()
        
        if not version_1 or not version_2:
            return error_response(msg="版本不存在", code=ErrorCodes.NOT_FOUND)
        
        # 构建对比数据
        comparison = {
            "version_1": {
                "id": version_1.id,
                "version_number": version_1.version_number,
                "training_status": version_1.training_status,
                "start_time": version_1.start_time.isoformat() if version_1.start_time else None,
                "complete_time": version_1.complete_time.isoformat() if version_1.complete_time else None,
                "intent_count": version_1.intent_count,
                "slot_count": version_1.slot_count,
                "training_data_count": version_1.training_data_count,
                "is_active": version_1.is_active
            },
            "version_2": {
                "id": version_2.id,
                "version_number": version_2.version_number,
                "training_status": version_2.training_status,
                "start_time": version_2.start_time.isoformat() if version_2.start_time else None,
                "complete_time": version_2.complete_time.isoformat() if version_2.complete_time else None,
                "intent_count": version_2.intent_count,
                "slot_count": version_2.slot_count,
                "training_data_count": version_2.training_data_count,
                "is_active": version_2.is_active
            },
            "differences": {
                "intent_count_diff": (version_2.intent_count or 0) - (version_1.intent_count or 0),
                "slot_count_diff": (version_2.slot_count or 0) - (version_1.slot_count or 0),
                "training_data_count_diff": (version_2.training_data_count or 0) - (version_1.training_data_count or 0)
            }
        }
        
        return success_response(data=comparison, msg="版本对比成功")
    
    except Exception as e:
        return error_response(msg=f"版本对比失败: {str(e)}", code=ErrorCodes.DATABASE_ERROR)

@router.get("/statistics/{library_id}")
async def get_version_statistics(
    library_id: int,
    db: Session = Depends(get_new_db)
):
    """获取版本统计"""
    try:
        # 检查指令库是否存在
        library = db.query(InstructionLibraryMaster).filter(
            InstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 获取版本统计
        versions = db.query(ModelTrainingRecord).filter(
            ModelTrainingRecord.library_id == library_id
        ).all()
        
        if not versions:
            statistics = {
                "library_id": library_id,
                "library_name": library.name,
                "total_versions": 0,
                "active_version": None,
                "latest_version": None,
                "successful_versions": 0,
                "failed_versions": 0,
                "training_versions": 0
            }
        else:
            # 计算统计信息
            active_version = None
            latest_version = None
            successful_count = 0
            failed_count = 0
            training_count = 0
            
            for version in versions:
                if version.is_active:
                    active_version = version.version_number
                if version.training_status == 'completed':
                    successful_count += 1
                elif version.training_status == 'failed':
                    failed_count += 1
                elif version.training_status == 'training':
                    training_count += 1
            
            # 最新版本
            latest_version_record = max(versions, key=lambda v: v.version_number)
            latest_version = latest_version_record.version_number
            
            statistics = {
                "library_id": library_id,
                "library_name": library.name,
                "total_versions": len(versions),
                "active_version": active_version,
                "latest_version": latest_version,
                "successful_versions": successful_count,
                "failed_versions": failed_count,
                "training_versions": training_count
            }
        
        return success_response(data=statistics, msg="获取版本统计成功")
    
    except Exception as e:
        return error_response(msg=f"获取版本统计失败: {str(e)}", code=ErrorCodes.DATABASE_ERROR) 