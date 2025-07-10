"""
智能对话训练平台 - 指令测试API
提供单条测试、批量测试和测试记录管理功能
基于现有功能进行适配，支持指令库和模型版本管理"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import pandas as pd
from io import BytesIO
import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.database_models import (
    get_new_db,
    InstructionLibraryMaster as DBInstructionLibraryMaster,
    ModelTrainingRecord as DBModelTrainingRecord,
    InstructionTestRecord as DBInstructionTestRecord,
    TestDetail as DBTestDetail
)
from response_utils import StandardResponse, success_response, error_response, ErrorCodes, Messages
from models.schemas import (
    SingleTestRequest, SingleTestResponse,
    BatchTestRequest, BatchTestResponse,
    InstructionTestRecord, InstructionTestRecordCreate,
    TestDetail, TestDetailCreate,
    ApiResponse,
    TestType, TestStatus
)
from services.rasa_service import get_rasa_service
from services.test_file_processor import get_test_file_processor

router = APIRouter(prefix="/api/v2/test", tags=["指令测试"])

# 获取RASA服务实例
rasa_service = get_rasa_service()
# 获取文件处理器实例
file_processor = get_test_file_processor()

# ===== 单条测试 =====

@router.post("/single", response_model=StandardResponse)
async def single_test(
    request: SingleTestRequest,
    db: Session = Depends(get_new_db)
):
    """
    单条指令测试
    
    Args:
        request: 包含library_id, model_version_id和测试文本
        
    Returns:
        SingleTestResponse: 测试结果
    """
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == request.library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 验证模型版本是否存在
        model_record = db.query(DBModelTrainingRecord).filter(
            DBModelTrainingRecord.id == request.model_version_id,
            DBModelTrainingRecord.library_id == request.library_id
        ).first()
        
        if not model_record:
            return error_response(msg="模型版本不存在", code=ErrorCodes.NOT_FOUND)
        
        # 执行单条测试
        prediction = rasa_service.predict_intent(
            request.input_text, 
            str(request.model_version_id)
        )
        
        # 构建响应
        return success_response(data={
            "intent": prediction.intent,
            "confidence": prediction.confidence,
            "entities": prediction.entities or [],
            "response_time": int(prediction.response_time)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        return error_response(msg="测试执行失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


# ===== 批量测试 =====

@router.post("/batch", response_model=StandardResponse)
async def batch_test(
    library_id: int = Form(...),
    model_version_id: int = Form(...),
    test_name: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_new_db)
):
    """
    批量指令测试
    
    Args:
        library_id: 指令库ID
        model_version_id: 模型版本ID
        test_name: 测试名称
        file: 测试文件(Excel或CSV)
        
    Returns:
        测试结果记录ID和统计信息
    """
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 验证模型版本是否存在
        model_record = db.query(DBModelTrainingRecord).filter(
            DBModelTrainingRecord.id == model_version_id,
            DBModelTrainingRecord.library_id == library_id
        ).first()
        
        if not model_record:
            return error_response(msg="模型版本不存在", code=ErrorCodes.NOT_FOUND)
        
        # 验证文件格式
        if not file_processor.validate_file_format(file.filename):
            return error_response(msg="不支持的文件格式，请上传Excel或CSV文件", code=ErrorCodes.INVALID_PARAMETER)
        
        # 读取文件内容
        file_content = await file.read()
        
        # 解析测试数据
        test_data = file_processor.read_test_file(file_content, file.filename)
        
        # 验证测试数据
        validation_result = file_processor.validate_test_data(test_data)
        if not validation_result['is_valid']:
            return error_response(
                msg=f"测试数据验证失败: {'; '.join(validation_result['errors'][:5])}", 
                code=ErrorCodes.INVALID_PARAMETER
            )
        
        # 使用有效的测试数据
        valid_test_data = validation_result['valid_data']
        
        # 创建测试记录
        test_record_data = InstructionTestRecordCreate(
            library_id=library_id,
            model_version_id=model_version_id,
            test_type=TestType.BATCH,
            test_name=test_name or f"批量测试_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            test_description=f"测试数据: {len(valid_test_data)} 条",
            total_count=len(valid_test_data),
            test_status=TestStatus.RUNNING
        )
        
        # 创建测试记录
        test_record = DBInstructionTestRecord(**test_record_data.dict())
        db.add(test_record)
        db.commit()
        db.refresh(test_record)
        
        # 执行批量测试
        success_count = 0
        total_confidence = 0.0
        
        for test_item in valid_test_data:
            text = test_item.get("text", "").strip()
            expected_intent = test_item.get("expected_intent")
            
            if not text:
                continue
            
            try:
                # 执行预测
                prediction = rasa_service.predict_intent(text, str(model_version_id))
                
                # 判断是否成功
                is_success = (
                    prediction.intent and 
                    prediction.intent not in ['nlu_fallback', 'out_of_scope'] and
                    (prediction.confidence or 0) >= 0.8  # 默认置信度阈值
                )
                
                if is_success:
                    success_count += 1
                    total_confidence += (prediction.confidence or 0)
                
                # 创建测试详情记录
                test_detail_data = TestDetailCreate(
                    test_record_id=test_record.id,
                    input_text=text,
                    expected_intent=expected_intent,
                    actual_intent=prediction.intent,
                    confidence_score=prediction.confidence,
                    extracted_entities=json.dumps(prediction.entities or [], ensure_ascii=False),
                    is_success=is_success,
                    response_time=int(prediction.response_time)
                )
                
                test_detail = DBTestDetail(**test_detail_data.dict())
                db.add(test_detail)
                
            except Exception as e:
                # 记录错误详情
                test_detail_data = TestDetailCreate(
                    test_record_id=test_record.id,
                    input_text=text,
                    expected_intent=expected_intent,
                    actual_intent=None,
                    confidence_score=None,
                    extracted_entities=None,
                    is_success=False,
                    error_message=str(e)
                )
                
                test_detail = DBTestDetail(**test_detail_data.dict())
                db.add(test_detail)
        
        # 计算统计信息
        total_count = len(valid_test_data)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        avg_confidence = (total_confidence / success_count) if success_count > 0 else 0
        
        # 更新测试记录
        test_record.success_count = success_count
        test_record.success_rate = success_rate
        test_record.avg_confidence = avg_confidence
        test_record.test_status = TestStatus.COMPLETED
        test_record.complete_time = datetime.now()
        
        db.commit()
        
        return success_response(data={
            "test_record_id": test_record.id,
            "total_count": total_count,
            "success_count": success_count,
            "success_rate": success_rate,
            "avg_confidence": avg_confidence,
            "message": f"批量测试完成，成功率: {success_rate:.1f}%"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        # 更新测试记录为失败状态
        if 'test_record' in locals():
            test_record.test_status = TestStatus.FAILED
            test_record.complete_time = datetime.now()
            db.commit()
        
        return error_response(msg="批量测试失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


# ===== 测试记录管理 =====

@router.get("/records")
async def get_test_records(
    library_id: int = Query(..., description="指令库ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    test_type: Optional[TestType] = Query(None),
    test_status: Optional[TestStatus] = Query(None),
    db: Session = Depends(get_new_db)
):
    """获取测试记录列表"""
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 构建查询
        query = db.query(DBInstructionTestRecord).filter(
            DBInstructionTestRecord.library_id == library_id
        )
        
        # 添加筛选条件
        if test_type:
            query = query.filter(DBInstructionTestRecord.test_type == test_type)
        
        if test_status:
            query = query.filter(DBInstructionTestRecord.test_status == test_status)
        
        # 排序和分页
        records = query.order_by(
            DBInstructionTestRecord.start_time.desc()
        ).offset(skip).limit(limit).all()
        
        # 转换为Pydantic模型
        result = []
        for record in records:
            record_dict = {
                "id": record.id,
                "library_id": record.library_id,
                "model_version_id": record.model_version_id,
                "test_type": record.test_type,
                "test_name": record.test_name,
                "test_description": record.test_description,
                "total_count": record.total_count,
                "success_count": record.success_count,
                "success_rate": record.success_rate,
                "avg_confidence": record.avg_confidence,
                "test_status": record.test_status,
                "test_report": record.test_report,
                "created_by": record.created_by,
                "start_time": record.start_time,
                "complete_time": record.complete_time
            }
            result.append(InstructionTestRecord(**record_dict))
        
        return success_response(data=result)
    except HTTPException:
        raise
    except Exception as e:
        return error_response(msg="获取测试记录失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


@router.get("/records/{record_id}")
async def get_test_record_detail(
    record_id: int,
    db: Session = Depends(get_new_db)
):
    """获取测试记录详情"""
    try:
        # 获取测试记录
        record = db.query(DBInstructionTestRecord).filter(
            DBInstructionTestRecord.id == record_id
        ).first()
        
        if not record:
            return error_response(msg="测试记录不存在", code=ErrorCodes.NOT_FOUND)
        
        # 获取测试详情
        test_details = db.query(DBTestDetail).filter(
            DBTestDetail.test_record_id == record_id
        ).order_by(DBTestDetail.test_time.asc()).all()
        
        # 构建响应
        return success_response(data={"record": record,
            "test_details": test_details,
            "total_details": len(test_details)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        return error_response(msg="获取测试详情失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


@router.delete("/records/{record_id}")
async def delete_test_record(
    record_id: int,
    db: Session = Depends(get_new_db)
):
    """删除测试记录"""
    try:
        # 获取测试记录
        record = db.query(DBInstructionTestRecord).filter(
            DBInstructionTestRecord.id == record_id
        ).first()
        
        if not record:
            return error_response(msg="测试记录不存在", code=ErrorCodes.NOT_FOUND)
        
        test_name = record.test_name
        
        # 删除测试记录(级联删除测试详情)
        db.delete(record)
        db.commit()
        
        return success_response(data={
            "success": True,
            "message": f"测试记录 '{test_name}' 删除成功",
            "deleted_record_id": record_id
        })
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return error_response(msg="删除测试记录失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


# ===== 统计功能 =====

@router.get("/library/{library_id}/summary")
async def get_test_summary(
    library_id: int,
    db: Session = Depends(get_new_db)
):
    """获取指令库测试汇总信息"""
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 获取测试统计
        total_tests = db.query(DBInstructionTestRecord).filter(
            DBInstructionTestRecord.library_id == library_id
        ).count()
        
        completed_tests = db.query(DBInstructionTestRecord).filter(
            DBInstructionTestRecord.library_id == library_id,
            DBInstructionTestRecord.test_status == TestStatus.COMPLETED
        ).count()
        
        return success_response(data={"library_id": library_id,
            "library_name": library.name,
            "total_tests": total_tests,
            "completed_tests": completed_tests,
            "pending_tests": total_tests - completed_tests
        })
        
    except HTTPException:
        raise
    except Exception as e:
        return error_response(msg="获取汇总信息失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


# ===== 模板下载 =====

@router.get("/template/download")
async def download_test_template():
    """下载测试模板"""
    try:
        # 生成测试模板
        template_df = file_processor.generate_test_template()
        
        # 转换为Excel格式
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            template_df.to_excel(writer, sheet_name='测试模板', index=False)
        
        output.seek(0)
        
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=测试模板.xlsx"}
        )
        
    except Exception as e:
        return error_response(msg=f"下载模板失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


# ===== 结果导出 =====

@router.get("/records/{record_id}/export")
async def export_test_results(
    record_id: int,
    db: Session = Depends(get_new_db)
):
    """导出测试结果"""
    try:
        # 获取测试记录
        record = db.query(DBInstructionTestRecord).filter(
            DBInstructionTestRecord.id == record_id
        ).first()
        
        if not record:
            return error_response(msg="测试记录不存在", code=ErrorCodes.NOT_FOUND)
        
        # 获取测试详情
        test_details = db.query(DBTestDetail).filter(
            DBTestDetail.test_record_id == record_id
        ).order_by(DBTestDetail.test_time.asc()).all()
        
        # 转换为导出格式
        export_data = []
        for detail in test_details:
            export_data.append({
                'input_text': detail.input_text,
                'expected_intent': detail.expected_intent,
                'actual_intent': detail.actual_intent,
                'confidence_score': detail.confidence_score,
                'is_success': detail.is_success,
                'response_time': detail.response_time,
                'extracted_entities': detail.extracted_entities,
                'error_message': detail.error_message
            })
        
        # 导出为Excel
        excel_content = file_processor.export_test_results(export_data)
        
        return StreamingResponse(
            BytesIO(excel_content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=测试结果_{record.test_name}.xlsx"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return error_response(msg=f"导出测试结果失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)
