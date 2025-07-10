"""
智能对话训练平台 - Pydantic数据模型
用于API请求和响应的数据验证和序列化
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


# ===== 枚举类型定义 =====

class TrainingStatus(str, Enum):
    """训练状态枚举"""
    PREPARING = "preparing"
    TRAINING = "training"
    SUCCESS = "success"
    FAILED = "failed"


class TestStatus(str, Enum):
    """测试状态枚举"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestType(str, Enum):
    """测试类型枚举"""
    SINGLE = "single"
    BATCH = "batch"
    COMPARISON = "comparison"


class SlotType(str, Enum):
    """词槽类型枚举"""
    CATEGORICAL = "categorical"
    TEXT = "text"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"


# ===== 指令库母版相关 =====

class InstructionLibraryMasterBase(BaseModel):
    """指令库母版基础模型"""
    name: str = Field(..., description="指令库名称", max_length=100)
    language: str = Field(..., description="语种", max_length=10)
    description: Optional[str] = Field(None, description="描述信息")
    business_code: Optional[str] = Field(None, description="业务编码", max_length=50)
    created_by: Optional[str] = Field(None, description="创建人", max_length=50)
    is_active: bool = Field(True, description="是否启用")


class InstructionLibraryMasterCreate(InstructionLibraryMasterBase):
    """创建指令库母版请求"""
    pass


class InstructionLibraryMasterUpdate(BaseModel):
    """更新指令库母版请求"""
    name: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = None
    business_code: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class InstructionLibraryMaster(InstructionLibraryMasterBase):
    """指令库母版响应"""
    id: int
    created_time: datetime
    updated_time: datetime
    instruction_count: Optional[int] = Field(None, description="指令数量")
    slot_count: Optional[int] = Field(None, description="词槽数量")
    latest_version: Optional[int] = Field(None, description="最新训练版本")

    class Config:
        from_attributes = True


# ===== 指令数据相关 =====

class InstructionDataBase(BaseModel):
    """指令数据基础模型"""
    instruction_name: str = Field(..., description="指令名称", max_length=100)
    instruction_code: str = Field(..., description="指令编码", max_length=50)
    instruction_desc: Optional[str] = Field(None, description="指令描述")
    category: Optional[str] = Field(None, description="指令分类", max_length=50)
    is_slot_related: bool = Field(False, description="是否关联词槽")
    related_slot_ids: Optional[str] = Field(None, description="关联的词槽ID列表(JSON格式)")
    success_response: Optional[str] = Field(None, description="执行成功话术")
    failure_response: Optional[str] = Field(None, description="执行失败话术")
    is_enabled: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, description="排序序号")


class InstructionDataCreate(InstructionDataBase):
    """创建指令数据请求"""
    library_id: int = Field(..., description="所属指令库ID")
    similar_questions: Optional[List[str]] = Field(None, description="相似问列表")


class InstructionDataUpdate(BaseModel):
    """更新指令数据请求"""
    instruction_name: Optional[str] = Field(None, max_length=100)
    instruction_code: Optional[str] = Field(None, max_length=50)
    instruction_desc: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    is_slot_related: Optional[bool] = None
    related_slot_ids: Optional[str] = None
    success_response: Optional[str] = None
    failure_response: Optional[str] = None
    is_enabled: Optional[bool] = None
    sort_order: Optional[int] = None


class InstructionData(InstructionDataBase):
    """指令数据响应"""
    id: int
    library_id: int
    created_time: datetime
    updated_time: datetime

    class Config:
        from_attributes = True


# ===== 相似问相关 =====

class SimilarQuestionBase(BaseModel):
    """相似问基础模型"""
    question_text: str = Field(..., description="相似问文本")
    is_enabled: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, description="排序序号")


class SimilarQuestionCreate(SimilarQuestionBase):
    """创建相似问请求"""
    pass


class SimilarQuestionUpdate(BaseModel):
    """更新相似问请求"""
    question_text: Optional[str] = None
    is_enabled: Optional[bool] = None
    sort_order: Optional[int] = None


class SimilarQuestion(SimilarQuestionBase):
    """相似问响应"""
    id: int
    instruction_id: int
    created_time: datetime

    class Config:
        from_attributes = True


# ===== 词槽定义相关 =====

class SlotDefinitionBase(BaseModel):
    """词槽定义基础模型"""
    slot_name: str = Field(..., description="词槽名称", max_length=100)
    slot_name_en: str = Field(..., description="词槽英文名", max_length=100)
    slot_type: SlotType = Field(..., description="词槽类型")
    description: Optional[str] = Field(None, description="词槽描述")
    is_required: bool = Field(False, description="是否必填")
    is_active: bool = Field(True, description="是否启用")
    is_system: bool = Field(False, description="是否为系统词槽")


class SlotDefinitionCreate(SlotDefinitionBase):
    """创建词槽定义请求"""
    library_id: int = Field(..., description="所属指令库ID")


class SlotDefinitionUpdate(BaseModel):
    """更新词槽定义请求"""
    slot_name: Optional[str] = Field(None, max_length=100)
    slot_name_en: Optional[str] = Field(None, max_length=100)
    slot_type: Optional[SlotType] = None
    description: Optional[str] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None
    is_system: Optional[bool] = None


class SlotDefinition(SlotDefinitionBase):
    """词槽定义响应"""
    id: int
    library_id: int
    created_time: datetime
    updated_time: datetime
    values_count: Optional[int] = Field(None, description="词槽值数量")

    class Config:
        from_attributes = True


# ===== 词槽值相关 =====

class SlotValueBase(BaseModel):
    """词槽值基础模型"""
    standard_value: str = Field(..., description="标准值", max_length=200)
    aliases: Optional[str] = Field(None, description="别名(用==分隔)")
    description: Optional[str] = Field(None, description="值描述")
    sort_order: int = Field(0, description="排序序号")


class SlotValueCreate(SlotValueBase):
    """创建词槽值请求"""
    slot_id: int = Field(..., description="所属词槽ID")


class SlotValueUpdate(BaseModel):
    """更新词槽值请求"""
    standard_value: Optional[str] = Field(None, max_length=200)
    aliases: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class SlotValue(SlotValueBase):
    """词槽值响应"""
    id: int
    slot_id: int
    created_time: datetime

    class Config:
        from_attributes = True


# ===== 模型训练记录相关 =====

class ModelTrainingRecordBase(BaseModel):
    """模型训练记录基础模型"""
    version_number: int = Field(..., description="版本号")
    training_status: TrainingStatus = Field(TrainingStatus.PREPARING, description="训练状态")
    intent_count: Optional[int] = Field(None, description="意图数量")
    slot_count: Optional[int] = Field(None, description="词槽数量")
    training_data_count: Optional[int] = Field(None, description="训练数据量")
    is_active: bool = Field(False, description="是否激活")
    model_file_path: Optional[str] = Field(None, description="模型文件路径", max_length=500)
    config_snapshot: Optional[str] = Field(None, description="训练时配置快照")
    training_log: Optional[str] = Field(None, description="训练日志")
    error_message: Optional[str] = Field(None, description="错误信息")
    training_params: Optional[str] = Field(None, description="训练参数")


class ModelTrainingRecordCreate(ModelTrainingRecordBase):
    """创建模型训练记录请求"""
    library_id: int = Field(..., description="所属指令库ID")


class ModelTrainingRecordUpdate(BaseModel):
    """更新模型训练记录请求"""
    training_status: Optional[TrainingStatus] = None
    intent_count: Optional[int] = None
    slot_count: Optional[int] = None
    training_data_count: Optional[int] = None
    is_active: Optional[bool] = None
    model_file_path: Optional[str] = Field(None, max_length=500)
    config_snapshot: Optional[str] = None
    training_log: Optional[str] = None
    error_message: Optional[str] = None
    training_params: Optional[str] = None


class ModelTrainingRecord(ModelTrainingRecordBase):
    """模型训练记录响应"""
    id: int
    library_id: int
    start_time: Optional[datetime]
    complete_time: Optional[datetime]
    created_time: datetime

    class Config:
        from_attributes = True


# ===== 指令测试记录相关 =====

class InstructionTestRecordBase(BaseModel):
    """指令测试记录基础模型"""
    test_type: TestType = Field(..., description="测试类型")
    test_name: Optional[str] = Field(None, description="测试名称", max_length=100)
    test_description: Optional[str] = Field(None, description="测试描述")
    total_count: Optional[int] = Field(None, description="总测试数量")
    success_count: Optional[int] = Field(None, description="成功数量")
    success_rate: Optional[float] = Field(None, description="成功率")
    avg_confidence: Optional[float] = Field(None, description="平均置信度")
    test_status: TestStatus = Field(TestStatus.RUNNING, description="测试状态")
    test_report: Optional[str] = Field(None, description="测试报告")
    created_by: Optional[str] = Field(None, description="创建人", max_length=50)


class InstructionTestRecordCreate(InstructionTestRecordBase):
    """创建指令测试记录请求"""
    library_id: int = Field(..., description="所属指令库ID")
    model_version_id: int = Field(..., description="测试使用的模型版本ID")


class InstructionTestRecordUpdate(BaseModel):
    """更新指令测试记录请求"""
    test_name: Optional[str] = Field(None, max_length=100)
    test_description: Optional[str] = None
    total_count: Optional[int] = None
    success_count: Optional[int] = None
    success_rate: Optional[float] = None
    avg_confidence: Optional[float] = None
    test_status: Optional[TestStatus] = None
    test_report: Optional[str] = None


class InstructionTestRecord(InstructionTestRecordBase):
    """指令测试记录响应"""
    id: int
    library_id: int
    model_version_id: int
    start_time: datetime
    complete_time: Optional[datetime]

    class Config:
        from_attributes = True


# ===== 测试详情相关 =====

class TestDetailBase(BaseModel):
    """测试详情基础模型"""
    input_text: str = Field(..., description="输入文本")
    expected_intent: Optional[str] = Field(None, description="期望意图", max_length=100)
    actual_intent: Optional[str] = Field(None, description="实际识别意图", max_length=100)
    confidence_score: Optional[float] = Field(None, description="置信度分数")
    extracted_entities: Optional[str] = Field(None, description="提取的实体")
    is_success: Optional[bool] = Field(None, description="是否识别成功")
    response_time: Optional[int] = Field(None, description="响应时间(毫秒)")
    error_message: Optional[str] = Field(None, description="错误信息")


class TestDetailCreate(TestDetailBase):
    """创建测试详情请求"""
    test_record_id: int = Field(..., description="所属测试记录ID")


class TestDetailUpdate(BaseModel):
    """更新测试详情请求"""
    expected_intent: Optional[str] = Field(None, max_length=100)
    actual_intent: Optional[str] = Field(None, max_length=100)
    confidence_score: Optional[float] = None
    extracted_entities: Optional[str] = None
    is_success: Optional[bool] = None
    response_time: Optional[int] = None
    error_message: Optional[str] = None


class TestDetail(TestDetailBase):
    """测试详情响应"""
    id: int
    test_record_id: int
    test_time: datetime

    class Config:
        from_attributes = True


# ===== 系统配置相关 =====

class SystemConfigBase(BaseModel):
    """系统配置基础模型"""
    config_key: str = Field(..., description="配置键", max_length=100)
    config_value: Optional[str] = Field(None, description="配置值")
    config_desc: Optional[str] = Field(None, description="配置描述")
    is_active: bool = Field(True, description="是否启用")


class SystemConfigCreate(SystemConfigBase):
    """创建系统配置请求"""
    pass


class SystemConfigUpdate(BaseModel):
    """更新系统配置请求"""
    config_value: Optional[str] = None
    config_desc: Optional[str] = None
    is_active: Optional[bool] = None


class SystemConfig(SystemConfigBase):
    """系统配置响应"""
    id: int
    updated_time: datetime

    class Config:
        from_attributes = True


# ===== 复合模型 =====

class InstructionDataDetail(InstructionData):
    """指令数据详情（包含相似问）"""
    similar_questions: List[SimilarQuestion] = []


class SlotDefinitionDetail(SlotDefinition):
    """词槽定义详情（包含词槽值）"""
    slot_values: List[SlotValue] = []


class InstructionLibraryMasterDetail(InstructionLibraryMaster):
    """指令库母版详情（包含统计信息）"""
    instruction_data: List[InstructionData] = []
    slot_definitions: List[SlotDefinition] = []
    training_records: List[ModelTrainingRecord] = []


# ===== 批量操作相关 =====

class BatchInstructionImport(BaseModel):
    """批量导入指令请求"""
    library_id: int = Field(..., description="指令库ID")
    instructions: List[Dict[str, Any]] = Field(..., description="指令数据列表")


class BatchImportResult(BaseModel):
    """批量导入结果"""
    success_count: int = Field(..., description="成功导入数量")
    failed_count: int = Field(..., description="失败数量")
    errors: List[str] = Field([], description="错误信息列表")
    imported_ids: List[int] = Field([], description="成功导入的ID列表")


# ===== 测试相关 =====

class SingleTestRequest(BaseModel):
    """单条测试请求"""
    library_id: int = Field(..., description="指令库ID")
    model_version_id: int = Field(..., description="模型版本ID")
    input_text: str = Field(..., description="测试文本")


class SingleTestResponse(BaseModel):
    """单条测试响应"""
    intent: Optional[str] = Field(None, description="识别的意图")
    confidence: Optional[float] = Field(None, description="置信度")
    entities: List[Dict[str, Any]] = Field([], description="实体列表")
    response_time: Optional[int] = Field(None, description="响应时间")


class BatchTestRequest(BaseModel):
    """批量测试请求"""
    library_id: int = Field(..., description="指令库ID")
    model_version_id: int = Field(..., description="模型版本ID")
    test_name: Optional[str] = Field(None, description="测试名称")
    test_data: List[Dict[str, str]] = Field(..., description="测试数据")


class BatchTestResponse(BaseModel):
    """批量测试响应"""
    test_record_id: int = Field(..., description="测试记录ID")
    total_count: int = Field(..., description="总测试数量")
    message: str = Field(..., description="响应消息")


# ===== 训练相关 =====

class TrainingStartRequest(BaseModel):
    """开始训练请求"""
    library_id: int = Field(..., description="指令库ID")
    training_params: Optional[Dict[str, Any]] = Field(None, description="训练参数")


class TrainingStartResponse(BaseModel):
    """开始训练响应"""
    training_record_id: int = Field(..., description="训练记录ID")
    version_number: int = Field(..., description="版本号")
    message: str = Field(..., description="响应消息")


class TrainingStatusResponse(BaseModel):
    """训练状态响应"""
    status: TrainingStatus = Field(..., description="训练状态")
    progress: Optional[float] = Field(None, description="进度百分比")
    current_step: Optional[str] = Field(None, description="当前步骤")
    elapsed_time: Optional[int] = Field(None, description="已用时间(秒)")
    estimated_remaining: Optional[int] = Field(None, description="预计剩余时间(秒)")


# ===== 版本管理相关 =====

class VersionActivateRequest(BaseModel):
    """版本激活请求"""
    library_id: int = Field(..., description="指令库ID")
    version_id: int = Field(..., description="版本ID")


class VersionCompareRequest(BaseModel):
    """版本对比请求"""
    library_id: int = Field(..., description="指令库ID")
    base_version_id: int = Field(..., description="基准版本ID")
    compare_version_id: int = Field(..., description="对比版本ID")


class VersionCompareResponse(BaseModel):
    """版本对比响应"""
    base_version: ModelTrainingRecord
    compare_version: ModelTrainingRecord
    data_changes: Dict[str, Any] = Field({}, description="数据变化")
    performance_changes: Dict[str, Any] = Field({}, description="性能变化")


# ===== 通用响应 =====

class ApiResponse(BaseModel):
    """通用API响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


class PaginatedResponse(BaseModel):
    """分页响应"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    items: List[Any] = Field(..., description="数据列表") 