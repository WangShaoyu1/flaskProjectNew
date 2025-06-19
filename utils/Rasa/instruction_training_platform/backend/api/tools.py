from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.schemas import (
    BatchTestRequest, BatchTestResponse, DataUploadRequest, DataUploadResponse,
    Model, TrainingTask
)
from services.rasa_service import RasaService
from services.data_service import DataImportService, DataExportService
from services.database_service import ModelService, TrainingTaskService
import json

router = APIRouter(prefix="/api/tools", tags=["tools"])

# 初始化服务
rasa_service = RasaService()

@router.post("/batch-test", response_model=BatchTestResponse)
async def batch_test(request: BatchTestRequest, db: Session = Depends(get_db)):
    """
    批量测试接口 - 使用测试数据集评估模型性能
    
    Args:
        request: 批量测试请求，包含测试数据和可选的模型版本
        
    Returns:
        BatchTestResponse: 测试结果，包含准确率、详细结果等
    """
    try:
        # 检查 Rasa 服务状态
        if not rasa_service.check_rasa_status():
            raise HTTPException(
                status_code=503, 
                detail="Rasa 服务不可用，请检查 Rasa 服务是否正常运行"
            )
        
        # 执行批量测试
        result = rasa_service.batch_test(request.test_data, request.model_version)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-data", response_model=DataUploadResponse)
async def upload_data(request: DataUploadRequest, db: Session = Depends(get_db)):
    """
    数据上传接口 - 支持 CSV、YAML、JSON 格式的训练数据导入
    
    Args:
        request: 数据上传请求，包含数据类型和内容
        
    Returns:
        DataUploadResponse: 导入结果统计
    """
    try:
        data_type = request.data_type.lower()
        content = request.content
        
        if data_type == "csv":
            result = DataImportService.import_csv_data(db, content)
        elif data_type == "yaml":
            result = DataImportService.import_yaml_data(db, content)
        elif data_type == "json":
            result = DataImportService.import_json_data(db, content)
        else:
            raise HTTPException(
                status_code=400, 
                detail="不支持的数据格式，支持的格式: csv, yaml, json"
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    文件上传接口 - 支持上传训练数据文件
    
    Args:
        file: 上传的文件
        
    Returns:
        DataUploadResponse: 导入结果统计
    """
    try:
        # 检查文件类型
        filename = file.filename.lower()
        content = await file.read()
        content_str = content.decode('utf-8')
        
        if filename.endswith('.csv'):
            result = DataImportService.import_csv_data(db, content_str)
        elif filename.endswith(('.yml', '.yaml')):
            result = DataImportService.import_yaml_data(db, content_str)
        elif filename.endswith('.json'):
            result = DataImportService.import_json_data(db, content_str)
        else:
            raise HTTPException(
                status_code=400, 
                detail="不支持的文件格式，支持的格式: .csv, .yml, .yaml, .json"
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export-data")
async def export_data(format: str = "rasa", db: Session = Depends(get_db)):
    """
    数据导出接口 - 导出训练数据为指定格式
    
    Args:
        format: 导出格式 (rasa, csv)
        
    Returns:
        Dict: 导出的数据
    """
    try:
        if format.lower() == "rasa":
            result = DataExportService.export_to_rasa_format(db)
            return {
                "format": "rasa",
                "data": result
            }
        elif format.lower() == "csv":
            csv_data = DataExportService.export_to_csv(db)
            return {
                "format": "csv",
                "data": csv_data
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail="不支持的导出格式，支持的格式: rasa, csv"
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_models(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    获取模型列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数限制
        
    Returns:
        List[Dict]: 模型列表
    """
    try:
        # 直接查询数据库，避免ORM序列化问题
        from database import engine
        with engine.connect() as conn:
            result = conn.execute(
                "SELECT id, version, file_path, training_time, data_version, status, metrics, is_active FROM models ORDER BY training_time DESC LIMIT ? OFFSET ?",
                (limit, skip)
            )
            models = []
            for row in result:
                models.append({
                    "id": row[0],
                    "version": row[1],
                    "file_path": row[2],
                    "training_time": row[3],
                    "data_version": row[4],
                    "status": row[5],
                    "metrics": row[6],
                    "is_active": bool(row[7])
                })
            return models
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@router.get("/models/active", response_model=Model)
async def get_active_model(db: Session = Depends(get_db)):
    """
    获取当前激活的模型
    
    Returns:
        Model: 当前激活的模型信息
    """
    try:
        active_model = ModelService.get_active_model(db)
        if not active_model:
            raise HTTPException(status_code=404, detail="没有找到激活的模型")
        
        return active_model
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{model_id}/activate")
async def activate_model(model_id: int, db: Session = Depends(get_db)):
    """
    激活指定模型
    
    Args:
        model_id: 模型ID
        
    Returns:
        Dict: 操作结果
    """
    try:
        success = ModelService.set_active_model(db, model_id)
        if not success:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        return {
            "message": "模型激活成功",
            "model_id": model_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training-tasks/{task_id}", response_model=TrainingTask)
async def get_training_task(task_id: str, db: Session = Depends(get_db)):
    """
    获取训练任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        TrainingTask: 训练任务信息
    """
    try:
        task = TrainingTaskService.get_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="训练任务不存在")
        
        return task
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-info")
async def get_system_info():
    """
    获取系统信息
    
    Returns:
        Dict: 系统状态信息
    """
    try:
        import psutil
        import platform
        
        # 获取系统基本信息
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:').percent
        }
        
        # 检查 GPU 信息
        try:
            import tensorflow as tf
            gpu_devices = tf.config.list_physical_devices('GPU')
            system_info["gpu_available"] = len(gpu_devices) > 0
            system_info["gpu_devices"] = [device.name for device in gpu_devices]
        except:
            system_info["gpu_available"] = False
            system_info["gpu_devices"] = []
        
        # 检查 Rasa 服务状态
        system_info["rasa_status"] = rasa_service.check_rasa_status()
        
        return system_info
        
    except Exception as e:
        return {
            "error": f"获取系统信息失败: {str(e)}"
        }

