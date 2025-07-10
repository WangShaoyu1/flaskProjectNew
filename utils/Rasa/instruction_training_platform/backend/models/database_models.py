from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os

# 新数据库模型 - 智能对话训练平台
Base = declarative_base()


class InstructionLibraryMaster(Base):
    """指令库母版表"""
    __tablename__ = "instruction_library_master"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment='指令库名称')
    language = Column(String(10), nullable=False, comment='语种(zh-CN, en-US等)')
    description = Column(Text, comment='描述信息')
    business_code = Column(String(50), comment='业务编码')
    created_by = Column(String(50), comment='创建人')
    created_time = Column(DateTime(timezone=True), server_default=func.now())
    updated_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # 关联关系
    instruction_data = relationship("InstructionData", back_populates="library", cascade="all, delete-orphan")
    slot_definitions = relationship("SlotDefinition", back_populates="library", cascade="all, delete-orphan")
    training_records = relationship("ModelTrainingRecord", back_populates="library", cascade="all, delete-orphan")
    test_records = relationship("InstructionTestRecord", back_populates="library", cascade="all, delete-orphan")


class InstructionData(Base):
    """指令数据表"""
    __tablename__ = "instruction_data"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("instruction_library_master.id"), nullable=False, comment='所属指令库ID')
    instruction_name = Column(String(100), nullable=False, comment='指令名称')
    instruction_code = Column(String(50), nullable=False, comment='指令编码')
    instruction_desc = Column(Text, comment='指令描述')
    category = Column(String(50), comment='指令分类')
    is_slot_related = Column(Boolean, default=False, comment='是否关联词槽')
    related_slot_ids = Column(Text, comment='关联的词槽ID列表(JSON格式)')
    success_response = Column(Text, comment='执行成功话术')
    failure_response = Column(Text, comment='执行失败话术')
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    sort_order = Column(Integer, default=0, comment='排序序号')
    created_time = Column(DateTime(timezone=True), server_default=func.now())
    updated_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    library = relationship("InstructionLibraryMaster", back_populates="instruction_data")
    similar_questions = relationship("SimilarQuestion", back_populates="instruction", cascade="all, delete-orphan")


class SimilarQuestion(Base):
    """相似问表"""
    __tablename__ = "similar_questions"

    id = Column(Integer, primary_key=True, index=True)
    instruction_id = Column(Integer, ForeignKey("instruction_data.id"), nullable=False, comment='所属指令ID')
    question_text = Column(Text, nullable=False, comment='相似问文本')
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    sort_order = Column(Integer, default=0, comment='排序序号')
    created_time = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    instruction = relationship("InstructionData", back_populates="similar_questions")


class SlotDefinition(Base):
    """词槽定义表"""
    __tablename__ = "slot_definitions"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("instruction_library_master.id"), nullable=False, comment='所属指令库ID')
    slot_name = Column(String(100), nullable=False, comment='词槽名称')
    slot_name_en = Column(String(100), nullable=False, comment='词槽英文名(用于RASA)')
    slot_type = Column(String(50), nullable=False, comment='词槽类型(categorical/text/float等)')
    description = Column(Text, comment='词槽描述')
    is_required = Column(Boolean, default=False, comment='是否必填')
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_system = Column(Boolean, default=False, comment='是否为系统词槽')
    created_time = Column(DateTime(timezone=True), server_default=func.now())
    updated_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联关系
    library = relationship("InstructionLibraryMaster", back_populates="slot_definitions")
    slot_values = relationship("SlotValue", back_populates="slot", cascade="all, delete-orphan")

    # 确保词槽英文名在指令库内唯一
    __table_args__ = (
        {"extend_existing": True}
    )


class SlotValue(Base):
    """词槽值表"""
    __tablename__ = "slot_values"

    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slot_definitions.id"), nullable=False, comment='所属词槽ID')
    standard_value = Column(String(200), nullable=False, comment='标准值')
    aliases = Column(Text, comment='别名(用==分隔)')
    description = Column(Text, comment='值描述')
    is_active = Column(Boolean, default=True, comment='是否启用')
    sort_order = Column(Integer, default=0, comment='排序序号')
    created_time = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    slot = relationship("SlotDefinition", back_populates="slot_values")


class ModelTrainingRecord(Base):
    """模型训练记录表"""
    __tablename__ = "model_training_records"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("instruction_library_master.id"), nullable=False, comment='所属指令库ID')
    version_number = Column(Integer, nullable=False, comment='版本号')
    training_status = Column(String(20), default='preparing', comment='训练状态(preparing/training/success/failed)')
    start_time = Column(DateTime(timezone=True), comment='开始时间')
    complete_time = Column(DateTime(timezone=True), comment='完成时间')
    intent_count = Column(Integer, comment='意图数量')
    slot_count = Column(Integer, comment='词槽数量')
    training_data_count = Column(Integer, comment='训练数据量')
    is_active = Column(Boolean, default=False, comment='是否激活')
    model_file_path = Column(String(500), comment='模型文件路径')
    config_snapshot = Column(Text, comment='训练时配置快照(JSON)')
    training_log = Column(Text, comment='训练日志')
    error_message = Column(Text, comment='错误信息')
    training_params = Column(Text, comment='训练参数(JSON)')
    created_time = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    library = relationship("InstructionLibraryMaster", back_populates="training_records")
    test_records = relationship("InstructionTestRecord", back_populates="model_version")

    # 确保版本号在指令库内唯一
    __table_args__ = (
        {"extend_existing": True}
    )


class InstructionTestRecord(Base):
    """指令测试记录表"""
    __tablename__ = "instruction_test_records"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("instruction_library_master.id"), nullable=False, comment='所属指令库ID')
    model_version_id = Column(Integer, ForeignKey("model_training_records.id"), nullable=False, comment='测试使用的模型版本ID')
    test_type = Column(String(20), nullable=False, comment='测试类型(single/batch/comparison)')
    test_name = Column(String(100), comment='测试名称')
    test_description = Column(Text, comment='测试描述')
    total_count = Column(Integer, comment='总测试数量')
    success_count = Column(Integer, comment='成功数量')
    success_rate = Column(Numeric(5, 2), comment='成功率')
    avg_confidence = Column(Numeric(5, 2), comment='平均置信度')
    test_status = Column(String(20), default='running', comment='测试状态(running/completed/failed)')
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    complete_time = Column(DateTime(timezone=True), comment='完成时间')
    test_report = Column(Text, comment='测试报告(JSON)')
    created_by = Column(String(50), comment='创建人')

    # 关联关系
    library = relationship("InstructionLibraryMaster", back_populates="test_records")
    model_version = relationship("ModelTrainingRecord", back_populates="test_records")
    test_details = relationship("TestDetail", back_populates="test_record", cascade="all, delete-orphan")


class TestDetail(Base):
    """测试详情表"""
    __tablename__ = "test_details"

    id = Column(Integer, primary_key=True, index=True)
    test_record_id = Column(Integer, ForeignKey("instruction_test_records.id"), nullable=False, comment='所属测试记录ID')
    input_text = Column(Text, nullable=False, comment='输入文本')
    expected_intent = Column(String(100), comment='期望意图')
    actual_intent = Column(String(100), comment='实际识别意图')
    confidence_score = Column(Numeric(5, 2), comment='置信度分数')
    extracted_entities = Column(Text, comment='提取的实体(JSON)')
    is_success = Column(Boolean, comment='是否识别成功')
    response_time = Column(Integer, comment='响应时间(毫秒)')
    error_message = Column(Text, comment='错误信息')
    test_time = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    test_record = relationship("InstructionTestRecord", back_populates="test_details")


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), nullable=False, unique=True)
    config_value = Column(Text)
    config_desc = Column(Text, comment='配置描述')
    is_active = Column(Boolean, default=True)
    updated_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ===== 向后兼容：保留现有模型结构 =====

class LegacyIntent(Base):
    """原有意图表（保留兼容性）"""
    __tablename__ = "intents"

    id = Column(Integer, primary_key=True, index=True)
    intent_name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    utterances = relationship("LegacyUtterance", back_populates="intent", cascade="all, delete-orphan")
    responses = relationship("LegacyResponse", back_populates="intent", cascade="all, delete-orphan")


class LegacyUtterance(Base):
    """原有相似问表（保留兼容性）"""
    __tablename__ = "utterances"

    id = Column(Integer, primary_key=True, index=True)
    intent_id = Column(Integer, ForeignKey("intents.id"), nullable=False)
    text = Column(Text, nullable=False)
    entities = Column(Text)  # JSON 格式存储实体标注信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    intent = relationship("LegacyIntent", back_populates="utterances")


class LegacyResponse(Base):
    """原有话术表（保留兼容性）"""
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    intent_id = Column(Integer, ForeignKey("intents.id"), nullable=False)
    type = Column(String(20), nullable=False)  # success, failure, fallback
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    intent = relationship("LegacyIntent", back_populates="responses")


class LegacyModel(Base):
    """原有模型表（保留兼容性）"""
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, nullable=False)
    file_path = Column(String(255), nullable=False)
    training_time = Column(DateTime(timezone=True), server_default=func.now())
    data_version = Column(String(50))
    status = Column(String(20), default="training")  # training, success, failed
    metrics = Column(Text)  # JSON 格式存储性能指标
    is_active = Column(Boolean, default=False)  # 是否为当前激活模型


class LegacyTrainingTask(Base):
    """原有训练任务表（保留兼容性）"""
    __tablename__ = "training_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    log_content = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    model_id = Column(Integer, ForeignKey("models.id"))


class LegacyUploadRecord(Base):
    """原有文件上传记录表（保留兼容性）"""
    __tablename__ = "upload_records"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # csv, xlsx, txt, json等
    file_size = Column(Integer, nullable=False)
    upload_type = Column(String(50), nullable=False)  # batch-test, training-data
    status = Column(String(20), nullable=False)  # success, error
    records_count = Column(Integer, default=0)  # 解析到的记录数
    error_message = Column(Text)
    parsed_data = Column(Text)  # JSON格式存储解析后的数据
    upload_time = Column(DateTime(timezone=True), server_default=func.now())


class LegacyBatchTestRecord(Base):
    """原有批量测试记录表（保留兼容性）"""
    __tablename__ = "batch_test_records"

    id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String(255))  # 测试名称（可选）
    total_tests = Column(Integer, nullable=False)  # 总测试数
    recognized_count = Column(Integer, nullable=False)  # 成功识别数量
    recognition_rate = Column(Float, nullable=False)  # 识别率
    confidence_threshold = Column(Float, nullable=False)  # 使用的置信度阈值
    test_data = Column(Text, nullable=False)  # JSON格式存储测试数据
    test_results = Column(Text, nullable=False)  # JSON格式存储测试结果
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# 数据库连接配置
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'instruction_platform_new.db'))}")

new_engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "isolation_level": None
    } if "sqlite" in DATABASE_URL else {},
    echo=False,
    encoding="utf-8"
)

NewSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=new_engine)


def create_new_tables():
    """创建新的数据库表结构"""
    Base.metadata.create_all(bind=new_engine)


def get_new_db():
    """新数据库会话依赖"""
    db = NewSessionLocal()
    try:
        yield db
    finally:
        db.close() 