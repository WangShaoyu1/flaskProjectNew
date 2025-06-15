from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.schemas import (
    Intent, IntentCreate, IntentUpdate, IntentDetail,
    Utterance, UtteranceCreate, UtteranceUpdate,
    Response, ResponseCreate, ResponseUpdate
)
from services.database_service import IntentService, UtteranceService, ResponseService

router = APIRouter(prefix="/api/intents", tags=["intents"])

@router.get("/", response_model=List[Intent])
async def get_intents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取意图列表"""
    return IntentService.get_intents(db, skip=skip, limit=limit)

@router.get("/{intent_id}", response_model=IntentDetail)
async def get_intent(intent_id: int, db: Session = Depends(get_db)):
    """获取意图详情（包含相似问和话术）"""
    intent = IntentService.get_intent(db, intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail="意图不存在")
    
    # 获取相似问和话术
    utterances = UtteranceService.get_utterances_by_intent(db, intent_id)
    responses = ResponseService.get_responses_by_intent(db, intent_id)
    
    return IntentDetail(
        id=intent.id,
        intent_name=intent.intent_name,
        description=intent.description,
        created_at=intent.created_at,
        updated_at=intent.updated_at,
        utterances=utterances,
        responses=responses
    )

@router.post("/", response_model=Intent)
async def create_intent(intent: IntentCreate, db: Session = Depends(get_db)):
    """创建意图"""
    # 检查意图名称是否已存在
    existing_intent = IntentService.get_intent_by_name(db, intent.intent_name)
    if existing_intent:
        raise HTTPException(status_code=400, detail="意图名称已存在")
    
    return IntentService.create_intent(db, intent)

@router.put("/{intent_id}", response_model=Intent)
async def update_intent(intent_id: int, intent: IntentUpdate, db: Session = Depends(get_db)):
    """更新意图"""
    # 检查意图是否存在
    existing_intent = IntentService.get_intent(db, intent_id)
    if not existing_intent:
        raise HTTPException(status_code=404, detail="意图不存在")
    
    # 如果更新意图名称，检查是否与其他意图重复
    if intent.intent_name and intent.intent_name != existing_intent.intent_name:
        duplicate_intent = IntentService.get_intent_by_name(db, intent.intent_name)
        if duplicate_intent:
            raise HTTPException(status_code=400, detail="意图名称已存在")
    
    updated_intent = IntentService.update_intent(db, intent_id, intent)
    if not updated_intent:
        raise HTTPException(status_code=404, detail="更新失败")
    
    return updated_intent

@router.delete("/{intent_id}")
async def delete_intent(intent_id: int, db: Session = Depends(get_db)):
    """删除意图"""
    success = IntentService.delete_intent(db, intent_id)
    if not success:
        raise HTTPException(status_code=404, detail="意图不存在")
    
    return {"message": "意图删除成功"}

# 相似问管理
@router.get("/{intent_id}/utterances", response_model=List[Utterance])
async def get_utterances(intent_id: int, db: Session = Depends(get_db)):
    """获取意图的相似问列表"""
    # 检查意图是否存在
    intent = IntentService.get_intent(db, intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail="意图不存在")
    
    return UtteranceService.get_utterances_by_intent(db, intent_id)

@router.post("/{intent_id}/utterances", response_model=Utterance)
async def create_utterance(intent_id: int, utterance: UtteranceCreate, db: Session = Depends(get_db)):
    """为意图添加相似问"""
    # 检查意图是否存在
    intent = IntentService.get_intent(db, intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail="意图不存在")
    
    # 设置意图ID
    utterance.intent_id = intent_id
    return UtteranceService.create_utterance(db, utterance)

@router.put("/utterances/{utterance_id}", response_model=Utterance)
async def update_utterance(utterance_id: int, utterance: UtteranceUpdate, db: Session = Depends(get_db)):
    """更新相似问"""
    updated_utterance = UtteranceService.update_utterance(db, utterance_id, utterance)
    if not updated_utterance:
        raise HTTPException(status_code=404, detail="相似问不存在")
    
    return updated_utterance

@router.delete("/utterances/{utterance_id}")
async def delete_utterance(utterance_id: int, db: Session = Depends(get_db)):
    """删除相似问"""
    success = UtteranceService.delete_utterance(db, utterance_id)
    if not success:
        raise HTTPException(status_code=404, detail="相似问不存在")
    
    return {"message": "相似问删除成功"}

# 话术管理
@router.get("/{intent_id}/responses", response_model=List[Response])
async def get_responses(intent_id: int, db: Session = Depends(get_db)):
    """获取意图的话术列表"""
    # 检查意图是否存在
    intent = IntentService.get_intent(db, intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail="意图不存在")
    
    return ResponseService.get_responses_by_intent(db, intent_id)

@router.post("/{intent_id}/responses", response_model=Response)
async def create_response(intent_id: int, response: ResponseCreate, db: Session = Depends(get_db)):
    """为意图添加话术"""
    # 检查意图是否存在
    intent = IntentService.get_intent(db, intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail="意图不存在")
    
    # 设置意图ID
    response.intent_id = intent_id
    return ResponseService.create_response(db, response)

@router.put("/responses/{response_id}", response_model=Response)
async def update_response(response_id: int, response: ResponseUpdate, db: Session = Depends(get_db)):
    """更新话术"""
    updated_response = ResponseService.update_response(db, response_id, response)
    if not updated_response:
        raise HTTPException(status_code=404, detail="话术不存在")
    
    return updated_response

@router.delete("/responses/{response_id}")
async def delete_response(response_id: int, db: Session = Depends(get_db)):
    """删除话术"""
    success = ResponseService.delete_response(db, response_id)
    if not success:
        raise HTTPException(status_code=404, detail="话术不存在")
    
    return {"message": "话术删除成功"}

