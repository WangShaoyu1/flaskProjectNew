from sqlalchemy.orm import Session
from database import Intent, Utterance, Response, Model, TrainingTask
from models.schemas import (
    IntentCreate, IntentUpdate, UtteranceCreate, UtteranceUpdate,
    ResponseCreate, ResponseUpdate, ModelCreate, TrainingTaskCreate
)
from typing import List, Optional
import json

class IntentService:
    """意图管理服务"""
    
    @staticmethod
    def get_intent(db: Session, intent_id: int) -> Optional[Intent]:
        return db.query(Intent).filter(Intent.id == intent_id).first()
    
    @staticmethod
    def get_intent_by_name(db: Session, intent_name: str) -> Optional[Intent]:
        return db.query(Intent).filter(Intent.intent_name == intent_name).first()
    
    @staticmethod
    def get_intents(db: Session, skip: int = 0, limit: int = 100) -> List[Intent]:
        return db.query(Intent).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_intent(db: Session, intent: IntentCreate) -> Intent:
        db_intent = Intent(**intent.dict())
        db.add(db_intent)
        db.commit()
        db.refresh(db_intent)
        return db_intent
    
    @staticmethod
    def update_intent(db: Session, intent_id: int, intent: IntentUpdate) -> Optional[Intent]:
        db_intent = db.query(Intent).filter(Intent.id == intent_id).first()
        if db_intent:
            for key, value in intent.dict(exclude_unset=True).items():
                setattr(db_intent, key, value)
            db.commit()
            db.refresh(db_intent)
        return db_intent
    
    @staticmethod
    def delete_intent(db: Session, intent_id: int) -> bool:
        db_intent = db.query(Intent).filter(Intent.id == intent_id).first()
        if db_intent:
            db.delete(db_intent)
            db.commit()
            return True
        return False

class UtteranceService:
    """相似问管理服务"""
    
    @staticmethod
    def get_utterances_by_intent(db: Session, intent_id: int) -> List[Utterance]:
        return db.query(Utterance).filter(Utterance.intent_id == intent_id).all()
    
    @staticmethod
    def create_utterance(db: Session, utterance: UtteranceCreate) -> Utterance:
        db_utterance = Utterance(**utterance.dict())
        db.add(db_utterance)
        db.commit()
        db.refresh(db_utterance)
        return db_utterance
    
    @staticmethod
    def update_utterance(db: Session, utterance_id: int, utterance: UtteranceUpdate) -> Optional[Utterance]:
        db_utterance = db.query(Utterance).filter(Utterance.id == utterance_id).first()
        if db_utterance:
            for key, value in utterance.dict(exclude_unset=True).items():
                setattr(db_utterance, key, value)
            db.commit()
            db.refresh(db_utterance)
        return db_utterance
    
    @staticmethod
    def delete_utterance(db: Session, utterance_id: int) -> bool:
        db_utterance = db.query(Utterance).filter(Utterance.id == utterance_id).first()
        if db_utterance:
            db.delete(db_utterance)
            db.commit()
            return True
        return False

class ResponseService:
    """话术管理服务"""
    
    @staticmethod
    def get_responses_by_intent(db: Session, intent_id: int) -> List[Response]:
        return db.query(Response).filter(Response.intent_id == intent_id).all()
    
    @staticmethod
    def create_response(db: Session, response: ResponseCreate) -> Response:
        db_response = Response(**response.dict())
        db.add(db_response)
        db.commit()
        db.refresh(db_response)
        return db_response
    
    @staticmethod
    def update_response(db: Session, response_id: int, response: ResponseUpdate) -> Optional[Response]:
        db_response = db.query(Response).filter(Response.id == response_id).first()
        if db_response:
            for key, value in response.dict(exclude_unset=True).items():
                setattr(db_response, key, value)
            db.commit()
            db.refresh(db_response)
        return db_response
    
    @staticmethod
    def delete_response(db: Session, response_id: int) -> bool:
        db_response = db.query(Response).filter(Response.id == response_id).first()
        if db_response:
            db.delete(db_response)
            db.commit()
            return True
        return False

class ModelService:
    """模型管理服务"""
    
    @staticmethod
    def get_models(db: Session, skip: int = 0, limit: int = 100) -> List[Model]:
        return db.query(Model).order_by(Model.training_time.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_active_model(db: Session) -> Optional[Model]:
        return db.query(Model).filter(Model.is_active == True).first()
    
    @staticmethod
    def create_model(db: Session, model: ModelCreate) -> Model:
        db_model = Model(**model.dict())
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        return db_model
    
    @staticmethod
    def set_active_model(db: Session, model_id: int) -> bool:
        # 先将所有模型设为非激活状态
        db.query(Model).update({Model.is_active: False})
        
        # 设置指定模型为激活状态
        db_model = db.query(Model).filter(Model.id == model_id).first()
        if db_model:
            db_model.is_active = True
            db.commit()
            return True
        return False

class TrainingTaskService:
    """训练任务管理服务"""
    
    @staticmethod
    def create_task(db: Session, task: TrainingTaskCreate) -> TrainingTask:
        db_task = TrainingTask(**task.dict())
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task
    
    @staticmethod
    def get_task(db: Session, task_id: str) -> Optional[TrainingTask]:
        return db.query(TrainingTask).filter(TrainingTask.task_id == task_id).first()
    
    @staticmethod
    def update_task_status(db: Session, task_id: str, status: str, progress: float = None, 
                          log_content: str = None, error_message: str = None) -> bool:
        db_task = db.query(TrainingTask).filter(TrainingTask.task_id == task_id).first()
        if db_task:
            db_task.status = status
            if progress is not None:
                db_task.progress = progress
            if log_content is not None:
                db_task.log_content = log_content
            if error_message is not None:
                db_task.error_message = error_message
            db.commit()
            return True
        return False

class UploadRecordService:
    """文件上传记录服务"""
    
    @staticmethod
    def create_record(db: Session, record_data: dict) -> 'UploadRecord':
        """创建上传记录"""
        from database import UploadRecord
        
        db_record = UploadRecord(**record_data)
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record
    
    @staticmethod
    def get_record(db: Session, record_id: int) -> Optional['UploadRecord']:
        """根据ID获取上传记录"""
        from database import UploadRecord
        
        return db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    
    @staticmethod
    def get_records(db: Session, skip: int = 0, limit: int = 20, upload_type: Optional[str] = None) -> List['UploadRecord']:
        """获取上传记录列表"""
        from database import UploadRecord
        
        query = db.query(UploadRecord)
        if upload_type:
            query = query.filter(UploadRecord.upload_type == upload_type)
        
        return query.order_by(UploadRecord.upload_time.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_records_count(db: Session, upload_type: Optional[str] = None) -> int:
        """获取上传记录总数"""
        from database import UploadRecord
        
        query = db.query(UploadRecord)
        if upload_type:
            query = query.filter(UploadRecord.upload_type == upload_type)
        
        return query.count()
    
    @staticmethod
    def update_record(db: Session, record_id: int, update_data: dict) -> bool:
        """更新上传记录"""
        from database import UploadRecord
        
        db_record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
        if not db_record:
            return False
        
        for key, value in update_data.items():
            if hasattr(db_record, key) and value is not None:
                setattr(db_record, key, value)
        
        db.commit()
        return True
    
    @staticmethod
    def delete_record(db: Session, record_id: int) -> bool:
        """删除上传记录"""
        from database import UploadRecord
        
        db_record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
        if not db_record:
            return False
        
        db.delete(db_record)
        db.commit()
        return True

class BatchTestRecordService:
    """批量测试记录服务"""
    
    @staticmethod
    def create_record(db: Session, record_data: dict) -> 'BatchTestRecord':
        """创建批量测试记录"""
        from database import BatchTestRecord
        
        db_record = BatchTestRecord(**record_data)
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record
    
    @staticmethod
    def get_record(db: Session, record_id: int) -> Optional['BatchTestRecord']:
        """根据ID获取批量测试记录"""
        from database import BatchTestRecord
        
        return db.query(BatchTestRecord).filter(BatchTestRecord.id == record_id).first()
    
    @staticmethod
    def get_records(db: Session, skip: int = 0, limit: int = 20) -> List['BatchTestRecord']:
        """获取批量测试记录列表"""
        from database import BatchTestRecord
        
        return db.query(BatchTestRecord).order_by(BatchTestRecord.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_records_count(db: Session) -> int:
        """获取批量测试记录总数"""
        from database import BatchTestRecord
        
        return db.query(BatchTestRecord).count()
    
    @staticmethod
    def get_latest_record(db: Session) -> Optional['BatchTestRecord']:
        """获取最新的批量测试记录"""
        from database import BatchTestRecord
        
        return db.query(BatchTestRecord).order_by(BatchTestRecord.created_at.desc()).first()
    
    @staticmethod
    def update_record(db: Session, record_id: int, update_data: dict) -> bool:
        """更新批量测试记录"""
        from database import BatchTestRecord
        
        db_record = db.query(BatchTestRecord).filter(BatchTestRecord.id == record_id).first()
        if not db_record:
            return False
        
        for key, value in update_data.items():
            if hasattr(db_record, key) and value is not None:
                setattr(db_record, key, value)
        
        db.commit()
        return True
    
    @staticmethod
    def delete_record(db: Session, record_id: int) -> bool:
        """删除批量测试记录"""
        from database import BatchTestRecord
        
        db_record = db.query(BatchTestRecord).filter(BatchTestRecord.id == record_id).first()
        if not db_record:
            return False
        
        db.delete(db_record)
        db.commit()
        return True

