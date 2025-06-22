from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# 基础模型
class IntentBase(BaseModel):
    intent_name: str
    description: Optional[str] = None

class IntentCreate(IntentBase):
    pass

class IntentUpdate(IntentBase):
    pass

class Intent(IntentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# 相似问模型
class UtteranceBase(BaseModel):
    text: str
    entities: Optional[str] = None

class UtteranceCreate(UtteranceBase):
    intent_id: int

class UtteranceUpdate(UtteranceBase):
    pass

class Utterance(UtteranceBase):
    id: int
    intent_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# 话术模型
class ResponseBase(BaseModel):
    type: str  # success, failure, fallback
    text: str

class ResponseCreate(ResponseBase):
    intent_id: int

class ResponseUpdate(ResponseBase):
    pass

class Response(ResponseBase):
    id: int
    intent_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# 模型管理
class ModelBase(BaseModel):
    version: str
    file_path: str
    data_version: Optional[str] = None
    status: str = "training"
    metrics: Optional[str] = None
    is_active: bool = False

class ModelCreate(ModelBase):
    pass

class Model(ModelBase):
    id: int
    training_time: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# 训练任务模型
class TrainingTaskBase(BaseModel):
    task_id: str
    status: str = "pending"
    progress: float = 0.0
    log_content: Optional[str] = None
    error_message: Optional[str] = None

class TrainingTaskCreate(TrainingTaskBase):
    pass

class TrainingTask(TrainingTaskBase):
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_id: Optional[int] = None
    
    class Config:
        from_attributes = True

# 预测请求和响应
class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    text: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    entities: List[Dict[str, Any]] = []
    raw_rasa_response: Dict[str, Any] = {}

# 训练请求
class TrainRequest(BaseModel):
    nlu_data: str
    domain_data: str
    force_retrain: bool = True

class TrainResponse(BaseModel):
    message: str
    task_id: str
    model_version: Optional[str] = None

# 批量测试 - 简化版
class BatchTestRequest(BaseModel):
    test_data: List[Dict[str, str]]  # [{"text": "..."}] 只需要测试文本
    confidence_threshold: Optional[float] = 0.8  # 置信度阈值
    test_name: Optional[str] = None  # 测试名称（可选）

class TestResult(BaseModel):
    text: str
    predicted_intent: Optional[str] = None
    confidence: Optional[float] = None
    response_time: Optional[float] = None  # 响应时间（毫秒）
    entities: Optional[List[Dict[str, Any]]] = []  # 实体信息

class BatchTestResponse(BaseModel):
    total_tests: int
    results: List[TestResult]

# 完整意图信息（包含相似问和话术）
class IntentDetail(Intent):
    utterances: List[Utterance] = []
    responses: List[Response] = []

# 数据上传
class DataUploadRequest(BaseModel):
    data_type: str  # "csv", "yaml", "json"
    content: str

class DataUploadResponse(BaseModel):
    message: str
    imported_intents: int
    imported_utterances: int
    imported_responses: int
    errors: List[str] = []
    upload_record_id: Optional[int] = None

# 文件上传记录模型
class UploadRecordBase(BaseModel):
    filename: str
    file_type: str  # csv, xlsx, txt, json等
    file_size: int
    upload_type: str  # batch-test, training-data
    status: str  # success, error
    records_count: int  # 解析到的记录数
    error_message: Optional[str] = None

class UploadRecordCreate(UploadRecordBase):
    parsed_data: Optional[str] = None  # JSON格式存储解析后的数据

class UploadRecordUpdate(BaseModel):
    status: Optional[str] = None
    records_count: Optional[int] = None
    error_message: Optional[str] = None
    parsed_data: Optional[str] = None

class UploadRecord(UploadRecordBase):
    id: int
    upload_time: datetime
    parsed_data: Optional[str] = None  # JSON格式存储解析后的数据
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# 上传记录列表响应
class UploadRecordListResponse(BaseModel):
    total: int
    records: List[Dict[str, Any]]  # 改为字典格式以避免序列化问题

# 上传记录详情响应
class UploadRecordDetailResponse(BaseModel):
    record: Dict[str, Any]  # 改为字典格式以避免序列化问题
    parsed_data_preview: List[Dict[str, Any]]  # 解析后数据的预览

# 批量测试记录模型
class BatchTestRecordBase(BaseModel):
    test_name: Optional[str] = None  # 测试名称（可选）
    total_tests: int
    recognized_count: int  # 成功识别数量
    recognition_rate: float  # 识别率
    confidence_threshold: float  # 使用的置信度阈值
    test_data: str  # JSON格式存储测试数据
    test_results: str  # JSON格式存储测试结果

class BatchTestRecordCreate(BatchTestRecordBase):
    pass

class BatchTestRecordUpdate(BaseModel):
    test_name: Optional[str] = None

class BatchTestRecord(BatchTestRecordBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# 批量测试记录列表响应
class BatchTestRecordListResponse(BaseModel):
    total: int
    records: List[Dict[str, Any]]

