from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.schemas import (
    BatchTestRequest, BatchTestResponse, DataUploadRequest, DataUploadResponse,
    Model, TrainingTask, UploadRecord, UploadRecordCreate, UploadRecordListResponse,
    UploadRecordDetailResponse
)
from services.rasa_service import RasaService
from services.data_service import DataImportService, DataExportService
from services.database_service import ModelService, TrainingTaskService, UploadRecordService, BatchTestRecordService
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
        result = rasa_service.batch_test(request.test_data, request.confidence_threshold)
        
        # 计算统计数据
        total_tests = result.total_tests
        recognized_count = 0
        
        for test_result in result.results:
            if (test_result.predicted_intent and 
                test_result.predicted_intent not in ['nlu_fallback', 'out_of_scope'] and
                (test_result.confidence or 0) >= request.confidence_threshold):
                recognized_count += 1
        
        recognition_rate = (recognized_count / total_tests) * 100 if total_tests > 0 else 0
        
        # 保存批量测试记录到数据库
        record_data = {
            "test_name": request.test_name,  # 添加测试名称
            "total_tests": total_tests,
            "recognized_count": recognized_count,
            "recognition_rate": recognition_rate,
            "confidence_threshold": request.confidence_threshold,
            "test_data": json.dumps([item.dict() if hasattr(item, 'dict') else item for item in request.test_data], ensure_ascii=False),
            "test_results": json.dumps([item.dict() if hasattr(item, 'dict') else item for item in result.results], ensure_ascii=False)
        }
        
        batch_record = BatchTestRecordService.create_record(db, record_data)
        
        # 在返回结果中添加记录ID
        response_data = result.dict() if hasattr(result, 'dict') else result
        response_data["batch_record_id"] = batch_record.id
        
        return response_data
        
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

@router.post("/upload-batch-test-file")
async def upload_batch_test_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    批量测试文件上传接口 - 专门处理测试数据文件的上传和解析
    
    Args:
        file: 上传的文件 (支持 .xlsx, .xls, .csv, .txt, .json)
        
    Returns:
        Dict: 包含解析后的测试数据和上传记录ID
    """
    upload_record_id = None
    try:
        # 检查文件类型
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
            
        filename = file.filename.lower()
        allowed_extensions = ['.xlsx', '.xls', '.csv', '.txt', '.json']
        
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式，支持的格式: {', '.join(allowed_extensions)}"
            )
        
        # 检查文件大小 (限制10MB)
        content = await file.read()
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail="文件大小不能超过10MB"
            )
        
        # 获取文件扩展名
        file_extension = filename.split('.')[-1] if '.' in filename else 'unknown'
        
        # 创建初始上传记录
        record_data = {
            "filename": file.filename,
            "file_type": file_extension,
            "file_size": len(content),
            "upload_type": "batch-test",
            "status": "processing",
            "records_count": 0
        }
        
        upload_record = UploadRecordService.create_record(db, record_data)
        upload_record_id = upload_record.id
        
        # 使用Excel处理器解析文件
        from services.excel_processor import ExcelProcessor
        
        try:
            if filename.endswith(('.xlsx', '.xls')):
                # Excel文件处理
                test_data = ExcelProcessor.extract_test_data_from_excel(content)
                
            elif filename.endswith('.csv'):
                # CSV文件处理
                content_str = ExcelProcessor.convert_csv_encoding(content)
                test_data = []
                
                for line in content_str.strip().split('\n'):
                    line = line.strip()
                    if line and line not in ['测试文本', 'text', '文本内容']:
                        # 处理CSV格式（取第一列）
                        text = line.split(',')[0].strip() if ',' in line else line
                        cleaned_text = ExcelProcessor.validate_and_clean_text(text)
                        if cleaned_text:
                            test_data.append({'text': cleaned_text})
                            
            elif filename.endswith('.txt'):
                # 文本文件处理
                content_str = ExcelProcessor.convert_csv_encoding(content)
                test_data = []
                
                for line in content_str.strip().split('\n'):
                    line = line.strip()
                    if line and line not in ['测试文本', 'text', '文本内容']:
                        cleaned_text = ExcelProcessor.validate_and_clean_text(line)
                        if cleaned_text:
                            test_data.append({'text': cleaned_text})
                            
            elif filename.endswith('.json'):
                # JSON文件处理
                content_str = content.decode('utf-8', errors='ignore')
                json_data = json.loads(content_str)
                test_data = []
                
                if isinstance(json_data, list):
                    for item in json_data:
                        if isinstance(item, str):
                            cleaned_text = ExcelProcessor.validate_and_clean_text(item)
                            if cleaned_text:
                                test_data.append({'text': cleaned_text})
                        elif isinstance(item, dict) and 'text' in item:
                            cleaned_text = ExcelProcessor.validate_and_clean_text(str(item['text']))
                            if cleaned_text:
                                test_data.append({'text': cleaned_text})
                else:
                    raise ValueError("JSON文件格式错误，应该是数组格式")
            
            # 更新上传记录为成功状态
            UploadRecordService.update_record(db, upload_record_id, {
                "status": "success",
                "records_count": len(test_data),
                "parsed_data": json.dumps(test_data, ensure_ascii=False)
            })
            
            return {
                "message": f"文件解析成功，提取到 {len(test_data)} 条测试数据",
                "test_data": test_data,
                "upload_record_id": upload_record_id,
                "file_info": {
                    "filename": file.filename,
                    "size": len(content),
                    "type": file_extension
                }
            }
            
        except json.JSONDecodeError as e:
            # 更新上传记录为失败状态
            if upload_record_id:
                UploadRecordService.update_record(db, upload_record_id, {
                    "status": "error",
                    "error_message": f"JSON文件格式错误: {str(e)}"
                })
            raise HTTPException(
                status_code=400,
                detail=f"JSON文件格式错误: {str(e)}"
            )
        except Exception as e:
            # 更新上传记录为失败状态
            if upload_record_id:
                UploadRecordService.update_record(db, upload_record_id, {
                    "status": "error",
                    "error_message": f"文件解析失败: {str(e)}"
                })
            raise HTTPException(
                status_code=400,
                detail=f"文件解析失败: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        # 更新上传记录为失败状态
        if upload_record_id:
            try:
                UploadRecordService.update_record(db, upload_record_id, {
                    "status": "error",
                    "error_message": f"文件处理失败: {str(e)}"
                })
            except:
                pass
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    训练数据文件上传接口 - 用于训练数据的导入
    
    Args:
        file: 上传的文件
        
    Returns:
        DataUploadResponse: 导入结果统计和上传记录ID
    """
    upload_record_id = None
    try:
        # 检查文件类型
        filename = file.filename.lower()
        content = await file.read()
        
        # 获取文件扩展名
        file_extension = filename.split('.')[-1] if '.' in filename else 'unknown'
        
        # 创建初始上传记录
        record_data = {
            "filename": file.filename,
            "file_type": file_extension,
            "file_size": len(content),
            "upload_type": "training-data",
            "status": "processing",
            "records_count": 0
        }
        
        upload_record = UploadRecordService.create_record(db, record_data)
        upload_record_id = upload_record.id
        
        # 处理文件编码
        try:
            if filename.endswith('.csv'):
                from services.excel_processor import ExcelProcessor
                try:
                    content_str = ExcelProcessor.convert_csv_encoding(content)
                except:
                    content_str = content.decode('utf-8', errors='ignore')
                result = DataImportService.import_csv_data(db, content_str)
                
            elif filename.endswith(('.yml', '.yaml')):
                content_str = content.decode('utf-8', errors='ignore')
                result = DataImportService.import_yaml_data(db, content_str)
                
            elif filename.endswith('.json'):
                content_str = content.decode('utf-8', errors='ignore')
                result = DataImportService.import_json_data(db, content_str)
                
            else:
                # 更新上传记录为失败状态
                UploadRecordService.update_record(db, upload_record_id, {
                    "status": "error",
                    "error_message": "不支持的文件格式，支持的格式: .csv, .yml, .yaml, .json"
                })
                raise HTTPException(
                    status_code=400, 
                    detail="不支持的文件格式，支持的格式: .csv, .yml, .yaml, .json"
                )
            
            # 更新上传记录为成功状态
            total_records = result.imported_intents + result.imported_utterances + result.imported_responses
            UploadRecordService.update_record(db, upload_record_id, {
                "status": "success",
                "records_count": total_records,
                "parsed_data": json.dumps({
                    "imported_intents": result.imported_intents,
                    "imported_utterances": result.imported_utterances,
                    "imported_responses": result.imported_responses,
                    "errors": result.errors
                }, ensure_ascii=False)
            })
            
            # 在返回结果中添加上传记录ID
            result.upload_record_id = upload_record_id
            return result
            
        except UnicodeDecodeError as e:
            # 更新上传记录为失败状态
            if upload_record_id:
                UploadRecordService.update_record(db, upload_record_id, {
                    "status": "error",
                    "error_message": f"文件编码错误: {str(e)}，请确保文件使用UTF-8编码"
                })
            raise HTTPException(
                status_code=400,
                detail=f"文件编码错误: {str(e)}，请确保文件使用UTF-8编码"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        # 更新上传记录为失败状态
        if upload_record_id:
            try:
                UploadRecordService.update_record(db, upload_record_id, {
                    "status": "error",
                    "error_message": f"文件处理失败: {str(e)}"
                })
            except:
                pass
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

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

@router.delete("/models/{model_id}")
async def delete_model(model_id: int, db: Session = Depends(get_db)):
    """
    删除指定模型
    
    Args:
        model_id: 模型ID
        
    Returns:
        Dict: 操作结果
    """
    try:
        # 检查模型是否存在
        model = ModelService.get_model(db, model_id)
        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        # 检查是否为激活模型
        if model.is_active:
            raise HTTPException(
                status_code=400, 
                detail="无法删除激活模型，请先激活其他模型"
            )
        
        # 执行删除
        success = ModelService.delete_model(db, model_id)
        if not success:
            raise HTTPException(
                status_code=500, 
                detail="删除模型失败，请检查日志获取详细信息"
            )
        
        return {
            "message": "模型删除成功",
            "model_id": model_id,
            "model_version": model.version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除模型时发生错误: {str(e)}")

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

# 上传记录相关API
@router.get("/upload-records")
async def get_upload_records(
    skip: int = 0, 
    limit: int = 20, 
    upload_type: str = None,
    db: Session = Depends(get_db)
):
    """
    获取文件上传记录列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数限制
        upload_type: 上传类型过滤 (batch-test, training-data)
        
    Returns:
        UploadRecordListResponse: 上传记录列表
    """
    try:
        records = UploadRecordService.get_records(db, skip=skip, limit=limit, upload_type=upload_type)
        total = UploadRecordService.get_records_count(db, upload_type=upload_type)
        
        # 转换为字典格式以避免序列化问题
        records_data = []
        for record in records:
            records_data.append({
                "id": record.id,
                "filename": record.filename,
                "file_type": record.file_type,
                "file_size": record.file_size,
                "upload_type": record.upload_type,
                "status": record.status,
                "records_count": record.records_count,
                "error_message": record.error_message,
                "parsed_data": record.parsed_data,
                "upload_time": record.upload_time.isoformat() if record.upload_time else None
            })
        
        return {
            "total": total,
            "records": records_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上传记录失败: {str(e)}")

@router.get("/upload-records/{record_id}")
async def get_upload_record_detail(record_id: int, db: Session = Depends(get_db)):
    """
    获取上传记录详情
    
    Args:
        record_id: 上传记录ID
        
    Returns:
        UploadRecordDetailResponse: 上传记录详情
    """
    try:
        record = UploadRecordService.get_record(db, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="上传记录不存在")
        
        # 解析存储的数据
        parsed_data_preview = []
        if record.parsed_data:
            try:
                parsed_data = json.loads(record.parsed_data)
                if isinstance(parsed_data, list):
                    # 批量测试数据，只显示前10条
                    parsed_data_preview = parsed_data[:10]
                elif isinstance(parsed_data, dict):
                    # 训练数据导入结果
                    parsed_data_preview = [parsed_data]
            except json.JSONDecodeError:
                parsed_data_preview = [{"error": "数据解析失败"}]
        
        # 转换记录为字典格式
        record_data = {
            "id": record.id,
            "filename": record.filename,
            "file_type": record.file_type,
            "file_size": record.file_size,
            "upload_type": record.upload_type,
            "status": record.status,
            "records_count": record.records_count,
            "error_message": record.error_message,
            "parsed_data": record.parsed_data,
            "upload_time": record.upload_time.isoformat() if record.upload_time else None
        }
        
        return {
            "record": record_data,
            "parsed_data_preview": parsed_data_preview
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上传记录详情失败: {str(e)}")

@router.delete("/upload-records/{record_id}")
async def delete_upload_record(record_id: int, db: Session = Depends(get_db)):
    """
    删除上传记录
    
    Args:
        record_id: 上传记录ID
        
    Returns:
        Dict: 删除结果
    """
    try:
        success = UploadRecordService.delete_record(db, record_id)
        if not success:
            raise HTTPException(status_code=404, detail="上传记录不存在")
        
        return {
            "message": "上传记录删除成功",
            "record_id": record_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除上传记录失败: {str(e)}")

@router.get("/upload-records/{record_id}/download")
async def download_upload_record_data(record_id: int, db: Session = Depends(get_db)):
    """
    下载上传记录的解析数据
    
    Args:
        record_id: 上传记录ID
        
    Returns:
        Dict: 完整的解析数据
    """
    try:
        record = UploadRecordService.get_record(db, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="上传记录不存在")
        
        if not record.parsed_data:
            raise HTTPException(status_code=404, detail="该记录没有解析数据")
        
        try:
            parsed_data = json.loads(record.parsed_data)
            return {
                "record_info": {
                    "id": record.id,
                    "filename": record.filename,
                    "upload_time": record.upload_time.isoformat(),
                    "upload_type": record.upload_type,
                    "records_count": record.records_count
                },
                "data": parsed_data
            }
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="解析数据格式错误")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载解析数据失败: {str(e)}")

# 批量测试记录相关API
@router.get("/batch-test-records")
async def get_batch_test_records(
    skip: int = 0, 
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取批量测试记录列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数限制
        
    Returns:
        BatchTestRecordListResponse: 批量测试记录列表
    """
    try:
        records = BatchTestRecordService.get_records(db, skip=skip, limit=limit)
        total = BatchTestRecordService.get_records_count(db)
        
        # 转换为字典格式以避免序列化问题
        records_data = []
        for record in records:
            records_data.append({
                "id": record.id,
                "test_name": record.test_name,
                "total_tests": record.total_tests,
                "recognized_count": record.recognized_count,
                "recognition_rate": record.recognition_rate,
                "confidence_threshold": record.confidence_threshold,
                "created_at": record.created_at.isoformat() if record.created_at else None
            })
        
        return {
            "total": total,
            "records": records_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取批量测试记录失败: {str(e)}")

@router.get("/batch-test-records/latest")
async def get_latest_batch_test_record(db: Session = Depends(get_db)):
    """
    获取最新的批量测试记录
    
    Returns:
        Dict: 最新的批量测试记录及其详细数据
    """
    try:
        record = BatchTestRecordService.get_latest_record(db)
        if not record:
            return {
                "message": "没有找到批量测试记录",
                "has_data": False
            }
        
        # 解析测试数据和结果
        test_data = []
        test_results = []
        
        try:
            if record.test_data:
                test_data = json.loads(record.test_data)
            if record.test_results:
                test_results = json.loads(record.test_results)
        except json.JSONDecodeError:
            pass
        
        return {
            "has_data": True,
            "record": {
                "id": record.id,
                "test_name": record.test_name,
                "total_tests": record.total_tests,
                "recognized_count": record.recognized_count,
                "recognition_rate": record.recognition_rate,
                "confidence_threshold": record.confidence_threshold,
                "created_at": record.created_at.isoformat() if record.created_at else None
            },
            "test_data": test_data,
            "test_results": test_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最新批量测试记录失败: {str(e)}")

@router.get("/batch-test-records/{record_id}")
async def get_batch_test_record_detail(record_id: int, db: Session = Depends(get_db)):
    """
    获取批量测试记录详情
    
    Args:
        record_id: 批量测试记录ID
        
    Returns:
        Dict: 批量测试记录详情和完整数据
    """
    try:
        record = BatchTestRecordService.get_record(db, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="批量测试记录不存在")
        
        # 解析测试数据和结果
        test_data = []
        test_results = []
        
        try:
            if record.test_data:
                test_data = json.loads(record.test_data)
            if record.test_results:
                test_results = json.loads(record.test_results)
        except json.JSONDecodeError:
            pass
        
        return {
            "record": {
                "id": record.id,
                "test_name": record.test_name,
                "total_tests": record.total_tests,
                "recognized_count": record.recognized_count,
                "recognition_rate": record.recognition_rate,
                "confidence_threshold": record.confidence_threshold,
                "created_at": record.created_at.isoformat() if record.created_at else None
            },
            "test_data": test_data,
            "test_results": test_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取批量测试记录详情失败: {str(e)}")

@router.delete("/batch-test-records/{record_id}")
async def delete_batch_test_record(record_id: int, db: Session = Depends(get_db)):
    """
    删除批量测试记录
    
    Args:
        record_id: 批量测试记录ID
        
    Returns:
        Dict: 删除结果
    """
    try:
        success = BatchTestRecordService.delete_record(db, record_id)
        if not success:
            raise HTTPException(status_code=404, detail="批量测试记录不存在")
        
        return {
            "message": "批量测试记录删除成功",
            "record_id": record_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除批量测试记录失败: {str(e)}")

@router.put("/batch-test-records/{record_id}")
async def update_batch_test_record(
    record_id: int, 
    test_name: str = None,
    db: Session = Depends(get_db)
):
    """
    更新批量测试记录
    
    Args:
        record_id: 批量测试记录ID
        test_name: 新的测试名称
        
    Returns:
        Dict: 更新结果
    """
    try:
        update_data = {}
        if test_name is not None:
            update_data["test_name"] = test_name
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供要更新的数据")
        
        success = BatchTestRecordService.update_record(db, record_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="批量测试记录不存在")
        
        return {
            "message": "批量测试记录更新成功",
            "record_id": record_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新批量测试记录失败: {str(e)}")

