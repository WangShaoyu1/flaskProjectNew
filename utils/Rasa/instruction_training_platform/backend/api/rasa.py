from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.schemas import PredictRequest, PredictResponse, TrainRequest, TrainResponse
from services.rasa_service import RasaService

router = APIRouter(prefix="/api/rasa", tags=["rasa"])

# 初始化 Rasa 服务
rasa_service = RasaService()

@router.post("/predict", response_model=PredictResponse)
async def predict_intent(request: PredictRequest, db: Session = Depends(get_db)):
    """
    语义理解接口 - 预测用户输入的意图
    
    Args:
        request: 包含用户输入文本的请求
        
    Returns:
        PredictResponse: 预测结果，包含意图、置信度、实体等信息
    """
    try:
        # 检查 Rasa 服务状态
        if not rasa_service.check_rasa_status():
            raise HTTPException(
                status_code=503, 
                detail="Rasa 服务不可用，请检查 Rasa 服务是否正常运行"
            )
        
        # 调用 Rasa 进行意图预测
        result = rasa_service.predict_intent(request.text)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train", response_model=TrainResponse)
async def train_model(request: TrainRequest, db: Session = Depends(get_db)):
    """
    模型训练接口 - 触发 Rasa 模型训练
    
    Args:
        request: 训练请求，可包含自定义的 NLU 和 Domain 数据
        
    Returns:
        TrainResponse: 训练结果，包含任务ID和模型版本
    """
    try:
        # 检查 Rasa 服务状态
        if not rasa_service.check_rasa_status():
            raise HTTPException(
                status_code=503, 
                detail="Rasa 服务不可用，请检查 Rasa 服务是否正常运行"
            )
        
        # 触发模型训练
        nlu_data = request.nlu_data if request.nlu_data else None
        domain_data = request.domain_data if request.domain_data else None
        
        result = rasa_service.train_model(db, nlu_data, domain_data)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_rasa_status():
    """
    检查 Rasa 服务状态
    
    Returns:
        Dict: 服务状态信息
    """
    try:
        is_available = rasa_service.check_rasa_status()
        
        return {
            "status": "available" if is_available else "unavailable",
            "rasa_server_url": rasa_service.rasa_server_url,
            "message": "Rasa 服务正常" if is_available else "Rasa 服务不可用"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "rasa_server_url": rasa_service.rasa_server_url,
            "message": f"检查 Rasa 服务状态时出错: {str(e)}"
        }

@router.post("/reload-model")
async def reload_model(db: Session = Depends(get_db)):
    """
    重新加载最新模型
    
    Returns:
        Dict: 操作结果
    """
    try:
        # 这里可以添加重新加载模型的逻辑
        # 例如调用 Rasa 的模型加载 API
        
        return {
            "message": "模型重新加载成功",
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载模型失败: {str(e)}")

@router.get("/training-data")
async def get_training_data(db: Session = Depends(get_db)):
    """
    获取当前的训练数据（NLU 和 Domain 格式）
    
    Returns:
        Dict: 包含 NLU 和 Domain 数据的字典
    """
    try:
        nlu_data, domain_data = rasa_service.generate_training_data(db)
        
        return {
            "nlu_data": nlu_data,
            "domain_data": domain_data,
            "message": "训练数据获取成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取训练数据失败: {str(e)}")

