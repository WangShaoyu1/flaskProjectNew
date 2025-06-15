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

