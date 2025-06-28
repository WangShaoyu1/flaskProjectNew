from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db, Intent, Utterance, Response
from models.schemas import (
    Intent, IntentCreate, IntentUpdate, IntentDetail,
    Utterance, UtteranceCreate, UtteranceUpdate,
    Response, ResponseCreate, ResponseUpdate
)
from services.database_service import IntentService, UtteranceService, ResponseService

router = APIRouter(prefix="/api/intents", tags=["intents"])

@router.get("/")
async def get_intents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取意图列表"""
    try:
        # 直接查询数据库，避免ORM序列化问题
        from database import engine
        with engine.connect() as conn:
            result = conn.execute(
                "SELECT id, intent_name, description, created_at, updated_at FROM intents ORDER BY id LIMIT ? OFFSET ?",
                (limit, skip)
            )
            intents = []
            for row in result:
                intents.append({
                    "id": row[0],
                    "intent_name": row[1],
                    "description": row[2] or "",
                    "created_at": row[3],
                    "updated_at": row[4]
                })
            return intents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取意图列表失败: {str(e)}")

@router.get("/utterances/all")
async def get_all_utterances(db: Session = Depends(get_db)):
    """获取所有相似问（包含所属意图信息）"""
    try:
        # 直接查询数据库，避免ORM序列化问题
        from database import engine
        with engine.connect() as conn:
            result = conn.execute(
                """
                SELECT u.id, u.text, u.entities, u.created_at, 
                       i.id as intent_id, i.intent_name, i.description
                FROM utterances u
                JOIN intents i ON u.intent_id = i.id
                ORDER BY i.intent_name, u.id
                """
            )
            utterances = []
            for row in result:
                utterances.append({
                    "id": row[0],
                    "text": row[1],
                    "entities": row[2],
                    "created_at": row[3],
                    "intent_id": row[4],
                    "intent_name": row[5],
                    "intent_description": row[6]
                })
            return utterances
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取所有相似问失败: {str(e)}")

@router.get("/{intent_id}")
async def get_intent(intent_id: int, db: Session = Depends(get_db)):
    """获取意图详情（包含相似问和话术）"""
    try:
        intent = IntentService.get_intent(db, intent_id)
        if not intent:
            raise HTTPException(status_code=404, detail="意图不存在")
        
        # 直接查询数据库，避免ORM序列化问题
        from database import engine
        import sqlalchemy as sa
        with engine.connect() as conn:
            # 获取相似问
            utterances_result = conn.execute(
                sa.text("SELECT id, text, entities, intent_id, created_at FROM utterances WHERE intent_id = :intent_id ORDER BY id"),
                {"intent_id": intent_id}
            )
            utterances = []
            for row in utterances_result:
                utterances.append({
                    "id": row[0],
                    "text": row[1],
                    "entities": row[2],
                    "intent_id": row[3],
                    "created_at": row[4]
                })
            
            # 获取话术
            responses_result = conn.execute(
                sa.text("SELECT id, type, text, intent_id, created_at FROM responses WHERE intent_id = :intent_id ORDER BY id"),
                {"intent_id": intent_id}
            )
            responses = []
            for row in responses_result:
                responses.append({
                    "id": row[0],
                    "type": row[1],
                    "text": row[2],
                    "intent_id": row[3],
                    "created_at": row[4]
                })
        
        return {
            "id": intent.id,
            "intent_name": intent.intent_name,
            "description": intent.description,
            "created_at": intent.created_at,
            "updated_at": intent.updated_at,
            "utterances": utterances,
            "responses": responses
        }
    except Exception as e:
        if "意图不存在" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"获取意图详情失败: {str(e)}")

@router.post("/")
async def create_intent(intent: IntentCreate, db: Session = Depends(get_db)):
    """创建意图"""
    try:
        # 检查意图名称是否已存在
        existing_intent = IntentService.get_intent_by_name(db, intent.intent_name)
        if existing_intent:
            raise HTTPException(status_code=400, detail="意图名称已存在")
        
        db_intent = IntentService.create_intent(db, intent)
        
        # 返回字典格式
        return {
            "id": db_intent.id,
            "intent_name": db_intent.intent_name,
            "description": db_intent.description,
            "created_at": db_intent.created_at,
            "updated_at": db_intent.updated_at
        }
    except Exception as e:
        if "意图名称已存在" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"创建意图失败: {str(e)}")

@router.put("/{intent_id}")
async def update_intent(intent_id: int, intent: IntentUpdate, db: Session = Depends(get_db)):
    """更新意图"""
    try:
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
        
        # 返回字典格式
        return {
            "id": updated_intent.id,
            "intent_name": updated_intent.intent_name,
            "description": updated_intent.description,
            "created_at": updated_intent.created_at,
            "updated_at": updated_intent.updated_at
        }
    except Exception as e:
        if "意图名称已存在" in str(e) or "意图不存在" in str(e) or "更新失败" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"更新意图失败: {str(e)}")

@router.delete("/{intent_id}")
async def delete_intent(intent_id: int, db: Session = Depends(get_db)):
    """删除意图"""
    success = IntentService.delete_intent(db, intent_id)
    if not success:
        raise HTTPException(status_code=404, detail="意图不存在")
    
    return {"message": "意图删除成功"}

# 相似问管理
@router.get("/{intent_id}/utterances")
async def get_utterances(intent_id: int):
    """获取意图的相似问列表"""
    import sqlite3
    import os
    
    try:
        # 直接使用sqlite3连接
        db_path = os.path.join(os.path.dirname(__file__), "../instruction_platform.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, text, entities, intent_id, created_at FROM utterances WHERE intent_id = ? ORDER BY id",
            (intent_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        # 构建响应
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "text": row[1],
                "entities": row[2],
                "intent_id": row[3],
                "created_at": row[4]
            })
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

@router.post("/{intent_id}/utterances")
async def create_utterance(intent_id: int, utterance: UtteranceCreate, db: Session = Depends(get_db)):
    """为意图添加相似问"""
    try:
        # 检查意图是否存在
        intent = IntentService.get_intent(db, intent_id)
        if not intent:
            raise HTTPException(status_code=404, detail="意图不存在")
        
        # 设置意图ID
        utterance.intent_id = intent_id
        db_utterance = UtteranceService.create_utterance(db, utterance)
        
        # 返回字典格式
        return {
            "id": db_utterance.id,
            "text": db_utterance.text,
            "entities": db_utterance.entities,
            "intent_id": db_utterance.intent_id,
            "created_at": db_utterance.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建相似问失败: {str(e)}")

@router.put("/utterances/{utterance_id}")
async def update_utterance(utterance_id: int, utterance: UtteranceUpdate, db: Session = Depends(get_db)):
    """更新相似问"""
    try:
        updated_utterance = UtteranceService.update_utterance(db, utterance_id, utterance)
        if not updated_utterance:
            raise HTTPException(status_code=404, detail="相似问不存在")
        
        # 返回字典格式
        return {
            "id": updated_utterance.id,
            "text": updated_utterance.text,
            "entities": updated_utterance.entities,
            "intent_id": updated_utterance.intent_id,
            "created_at": updated_utterance.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新相似问失败: {str(e)}")

@router.delete("/utterances/{utterance_id}")
async def delete_utterance(utterance_id: int, db: Session = Depends(get_db)):
    """删除相似问"""
    success = UtteranceService.delete_utterance(db, utterance_id)
    if not success:
        raise HTTPException(status_code=404, detail="相似问不存在")
    
    return {"message": "相似问删除成功"}

# 话术管理
@router.get("/{intent_id}/responses")
async def get_responses(intent_id: int, db: Session = Depends(get_db)):
    """获取意图的话术列表"""
    try:
        # 检查意图是否存在
        intent = IntentService.get_intent(db, intent_id)
        if not intent:
            raise HTTPException(status_code=404, detail="意图不存在")
        
        # 直接查询数据库，避免ORM序列化问题
        from database import engine
        import sqlalchemy as sa
        with engine.connect() as conn:
            result = conn.execute(
                sa.text("SELECT id, type, text, intent_id, created_at FROM responses WHERE intent_id = :intent_id ORDER BY id"),
                {"intent_id": intent_id}
            )
            responses = []
            for row in result:
                responses.append({
                    "id": row[0],
                    "type": row[1],
                    "text": row[2],
                    "intent_id": row[3],
                    "created_at": row[4]
                })
            return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取话术列表失败: {str(e)}")

@router.post("/{intent_id}/responses")
async def create_response(intent_id: int, response: ResponseCreate, db: Session = Depends(get_db)):
    """为意图添加话术"""
    try:
        # 检查意图是否存在
        intent = IntentService.get_intent(db, intent_id)
        if not intent:
            raise HTTPException(status_code=404, detail="意图不存在")
        
        # 设置意图ID
        response.intent_id = intent_id
        db_response = ResponseService.create_response(db, response)
        
        # 返回字典格式
        return {
            "id": db_response.id,
            "type": db_response.type,
            "text": db_response.text,
            "intent_id": db_response.intent_id,
            "created_at": db_response.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建话术失败: {str(e)}")

@router.put("/responses/{response_id}")
async def update_response(response_id: int, response: ResponseUpdate, db: Session = Depends(get_db)):
    """更新话术"""
    try:
        updated_response = ResponseService.update_response(db, response_id, response)
        if not updated_response:
            raise HTTPException(status_code=404, detail="话术不存在")
        
        # 返回字典格式
        return {
            "id": updated_response.id,
            "type": updated_response.type,
            "text": updated_response.text,
            "intent_id": updated_response.intent_id,
            "created_at": updated_response.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新话术失败: {str(e)}")

@router.delete("/responses/{response_id}")
async def delete_response(response_id: int, db: Session = Depends(get_db)):
    """删除话术"""
    success = ResponseService.delete_response(db, response_id)
    if not success:
        raise HTTPException(status_code=404, detail="话术不存在")
    
    return {"message": "话术删除成功"}

@router.get("/test-db")
async def test_db():
    """测试数据库连接"""
    try:
        from database import engine
        with engine.connect() as conn:
            result = conn.execute("SELECT COUNT(*) FROM utterances")
            count = result.fetchone()[0]
            return {"message": "数据库连接正常", "utterances_count": count}
    except Exception as e:
        return {"error": str(e)}

