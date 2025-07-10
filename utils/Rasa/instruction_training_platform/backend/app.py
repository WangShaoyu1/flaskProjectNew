#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能对话训练平台 - 新版本主应用
基于新的数据库结构和API设计
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# 设置编码
import locale
import json

# 注释掉有问题的编码设置
# # 确保UTF-8编码
# if sys.platform.startswith('win'):
#     # Windows下设置控制台编码
#     import codecs
#     sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
#     sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
import uvicorn

# 导入数据库初始化
from models.database_models import create_new_tables

# 导入CDN配置
from cdn_config import get_current_cdn_config

# 导入统一响应格式
from utils.response_utils import StandardResponse, success_response, error_response, ErrorCodes, Messages

# 导入日志系统
from middleware.logging_middleware import LoggingMiddleware, SystemEventLogger, ConsoleLoggingMiddleware
from utils.logger import log_system, log_error, setup_logger

# 导入API路由
from api.instruction_library import router as library_router
from api.instruction_data import router as instruction_router
from api.slot_management import router as slot_router
from api.instruction_test import router as test_router
from api.model_training import router as training_router
from api.version_management import router as version_router
from api.system_monitor import router as system_router
from api.dual_screen_import import router as dual_screen_router
from api.log_viewer import router as log_viewer_router
from api.library_version import router as library_version_router


# 设置控制台日志格式
def setup_console_logging():
    """设置控制台日志输出"""
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # 设置uvicorn日志
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(logging.INFO)

    # 设置uvicorn.access日志
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(logging.INFO)


# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("\n" + "=" * 60)
    print("🚀 启动智能对话训练平台 v2.0.0")
    print("=" * 60)
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📋 服务信息:")
    print("   - 后端API服务: http://localhost:8001")
    print("   - API文档: http://localhost:8001/docs")
    print("   - 健康检查: http://localhost:8001/api/health")
    print("=" * 60)

    SystemEventLogger.log_startup()

    # 确保数据库表存在
    try:
        create_new_tables()
        print("✅ 数据库表检查完成")
        SystemEventLogger.log_database_init()
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        SystemEventLogger.log_database_error(e)
        raise

    print("🎯 服务已启动，等待请求...")
    print("=" * 60)
    yield

    # 关闭时执行
    print("\n" + "=" * 60)
    print("📴 智能对话训练平台已关闭")
    print(f"⏰ 关闭时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    SystemEventLogger.log_shutdown()


# 创建FastAPI应用（禁用默认文档URL）
app = FastAPI(
    title="智能对话训练平台",
    description="基于RASA的智能对话模型训练和管理平台",
    version="2.0.0",
    docs_url=None,  # 禁用默认文档
    redoc_url=None,  # 禁用默认ReDoc
    lifespan=lifespan
)


# 自定义JSON响应类，确保UTF-8编码
class UTF8JSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            jsonable_encoder(content),
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


# 设置默认响应类
app.response_class = UTF8JSONResponse

# 添加控制台日志中间件（用于显示请求信息）
app.add_middleware(ConsoleLoggingMiddleware)

# 添加文件日志中间件
app.add_middleware(LoggingMiddleware)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 自定义Swagger UI文档页面（使用国内CDN）
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    cdn_config = get_current_cdn_config()
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url=cdn_config["swagger_js"],
        swagger_css_url=cdn_config["swagger_css"],
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


# 自定义ReDoc文档页面（使用国内CDN）
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    cdn_config = get_current_cdn_config()
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url=cdn_config["redoc_js"],
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


# 注册API路由
app.include_router(library_router)
app.include_router(instruction_router)
app.include_router(slot_router)
app.include_router(test_router)
app.include_router(training_router)
app.include_router(version_router)
app.include_router(system_router)
app.include_router(dual_screen_router)
app.include_router(log_viewer_router)
app.include_router(library_version_router)


# 根路径
@app.get("/", response_model=StandardResponse)
async def root():
    """根路径 - 系统状态"""
    data = {
        "name": "智能对话训练平台",
        "version": "2.0.0",
        "status": "运行中",
        "description": "基于RASA的智能对话模型训练和管理平台",
        "docs": "/docs",
        "redoc": "/redoc",
        "note": "文档页面已优化为使用国内CDN，无需VPN即可访问"
    }
    return success_response(data=data, msg="系统运行正常")


# 健康检查
@app.get("/api/health", response_model=StandardResponse)
async def health_check():
    """健康检查接口"""
    try:
        # 这里可以添加数据库连接检查等
        data = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "database": "connected",
            "version": "2.0.0"
        }
        return success_response(data=data, msg="服务健康状态良好")
    except Exception as e:
        return error_response(msg=f"服务不可用: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


# API版本信息
@app.get("/api/version", response_model=StandardResponse)
async def get_version():
    """获取API版本信息"""
    data = {
        "api_version": "2.0.0",
        "platform_version": "2.0.0",
        "build_date": "2024-01-01",
        "features": [
            "指令库母版管理",
            "指令数据管理",
            "词槽管理",
            "模型训练",
            "指令测试",
            "版本管理",
            "系统性能监控",
            "双屏数据导入"
        ]
    }
    return success_response(data=data, msg="获取版本信息成功")


if __name__ == "__main__":
    # 设置控制台日志
    setup_console_logging()

    print("=" * 60)
    print("🚀 启动智能对话训练平台 v2.0.0")
    print("=" * 60)
    print("📖 API文档: http://localhost:8001/docs (国内CDN优化)")
    print("📚 ReDoc文档: http://localhost:8001/redoc (国内CDN优化)")
    print("💡 健康检查: http://localhost:8001/api/health")
    print("🌐 无需VPN即可访问文档页面")
    print("=" * 60)

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
        access_log=True
    )
