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

# 批量测试
class BatchTestRequest(BaseModel):
    test_data: List[Dict[str, str]]  # [{"text": "...", "expected_intent": "..."}]
    model_version: Optional[str] = None

class TestResult(BaseModel):
    text: str
    expected_intent: str
    predicted_intent: Optional[str] = None
    confidence: Optional[float] = None
    is_correct: bool = False

class BatchTestResponse(BaseModel):
    total_tests: int
    correct_predictions: int
    accuracy: float
    results: List[TestResult]
    confusion_matrix: Optional[Dict[str, Any]] = None

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

