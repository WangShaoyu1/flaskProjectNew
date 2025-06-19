from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os
import logging

# 导入数据库和API路由
from database import create_tables
from api import intents, rasa, tools
from api_docs import custom_openapi

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的初始化操作
    try:
        # 创建数据库表
        create_tables()
        logger.info("数据库表创建成功")
        
        # 检查 Rasa 项目目录
        rasa_project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "rasa")
        )
        
        if not os.path.exists(rasa_project_root):
            logger.warning(f"Rasa 项目目录不存在: {rasa_project_root}")
        else:
            logger.info(f"Rasa 项目目录: {rasa_project_root}")
        
        logger.info("指令训练平台后端服务启动成功")
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise
    
    yield
    
    # 关闭时的清理操作
    logger.info("指令训练平台后端服务正在关闭...")

# 创建 FastAPI 应用
app = FastAPI(
    title="指令训练平台 API",
    description="基于 Rasa 3.6.21 的智能指令训练平台后端服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置 CORS - 允许所有来源以解决跨域问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=False,  # 当allow_origins=["*"]时，必须设置为False
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(intents.router)
app.include_router(rasa.router)
app.include_router(tools.router)

# 设置自定义 OpenAPI 文档
app.openapi = lambda: custom_openapi(app)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"}
    )

@app.get("/")
async def root():
    """根路径 - 服务健康检查"""
    return {
        "message": "指令训练平台后端服务",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 这里可以添加更多的健康检查逻辑
        # 例如检查数据库连接、Rasa 服务状态等
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "services": {
                "database": "connected",
                "rasa": "checking..."
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="服务不健康")

@app.get("/api/info")
async def get_api_info():
    """获取 API 信息"""
    return {
        "title": "指令训练平台 API",
        "version": "1.0.0",
        "description": "基于 Rasa 3.6.21 的智能指令训练平台",
        "endpoints": {
            "intents": "/api/intents",
            "rasa": "/api/rasa", 
            "tools": "/api/tools"
        },
        "features": [
            "意图管理",
            "相似问管理", 
            "话术管理",
            "模型训练",
            "语义理解",
            "批量测试",
            "数据导入导出"
        ],
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        }
    }



if __name__ == "__main__":
    # 获取配置参数
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8081))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"启动服务: http://{host}:{port}")
    logger.info(f"API 文档: http://{host}:{port}/docs")
    logger.info(f"ReDoc 文档: http://{host}:{port}/redoc")
    
    # 启动服务
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )

