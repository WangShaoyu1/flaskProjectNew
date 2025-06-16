from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./instruction_platform.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 数据模型定义
class Intent(Base):
    """意图表"""
    __tablename__ = "intents"

    id = Column(Integer, primary_key=True, index=True)
    intent_name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    utterances = relationship("Utterance", back_populates="intent", cascade="all, delete-orphan")
    responses = relationship("Response", back_populates="intent", cascade="all, delete-orphan")


class Utterance(Base):
    """相似问表"""
    __tablename__ = "utterances"

    id = Column(Integer, primary_key=True, index=True)
    intent_id = Column(Integer, ForeignKey("intents.id"), nullable=False)
    text = Column(Text, nullable=False)
    entities = Column(Text)  # JSON 格式存储实体标注信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    intent = relationship("Intent", back_populates="utterances")


class Response(Base):
    """话术表"""
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    intent_id = Column(Integer, ForeignKey("intents.id"), nullable=False)
    type = Column(String(20), nullable=False)  # success, failure, fallback
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    intent = relationship("Intent", back_populates="responses")


class Model(Base):
    """模型表"""
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, nullable=False)
    file_path = Column(String(255), nullable=False)
    training_time = Column(DateTime(timezone=True), server_default=func.now())
    data_version = Column(String(50))
    status = Column(String(20), default="training")  # training, success, failed
    metrics = Column(Text)  # JSON 格式存储性能指标
    is_active = Column(Boolean, default=False)  # 是否为当前激活模型


class TrainingTask(Base):
    """训练任务表"""
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


# 创建所有表
def create_tables():
    Base.metadata.create_all(bind=engine)
