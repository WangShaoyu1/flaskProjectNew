#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 文档配置
为 FastAPI 应用添加详细的 API 文档
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    """自定义 OpenAPI 文档"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="指令训练平台 API",
        version="1.0.0",
        description="""
## 基于 Rasa 3.6.21 的智能指令训练平台

### 功能特性
- 🎯 **意图管理**: 创建、编辑、删除意图定义
- 💬 **相似问管理**: 为每个意图添加训练语句
- 🗨️ **话术管理**: 配置意图对应的响应内容
- 🤖 **模型训练**: 基于训练数据生成 Rasa 模型
- 🧠 **语义理解**: 使用训练好的模型进行意图识别
- 🧪 **批量测试**: 评估模型性能和准确率
- 📊 **数据导入导出**: 支持多种格式的数据处理

### 技术架构
- **后端**: FastAPI + SQLAlchemy + SQLite
- **NLU引擎**: Rasa 3.6.21
- **前端**: React + Ant Design
- **数据库**: SQLite (可扩展至 PostgreSQL/MySQL)

### API 版本
当前版本: v1.0.0

### 认证方式
目前为开发环境，暂未启用认证。生产环境建议使用 JWT 或 OAuth2。

### 错误处理
所有 API 都遵循标准的 HTTP 状态码:
- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `422`: 数据验证失败
- `500`: 服务器内部错误

### 联系方式
- 开发团队: AI 训练平台团队
- 技术支持: support@example.com
        """,
        routes=app.routes,
        tags=[
            {
                "name": "intents",
                "description": "意图管理相关接口，包括意图的增删改查、相似问管理、话术管理等功能"
            },
            {
                "name": "rasa",
                "description": "Rasa 服务相关接口，包括模型训练、预测、状态检查等功能"
            },
            {
                "name": "tools",
                "description": "工具类接口，包括模型管理、数据导入导出、批量测试等功能"
            }
        ]
    )

    # 添加服务器信息
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8081",
            "description": "开发环境"
        },
        {
            "url": "http://your-domain.com",
            "description": "生产环境"
        }
    ]

    # 添加额外信息
    openapi_schema["info"]["contact"] = {
        "name": "API 支持",
        "email": "support@example.com"
    }

    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# API 响应示例
RESPONSE_EXAMPLES = {
    "intent_list": {
        "summary": "意图列表响应示例",
        "value": [
            {
                "id": 1,
                "intent_name": "greet",
                "description": "问候意图",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z"
            },
            {
                "id": 2,
                "intent_name": "goodbye",
                "description": "告别意图",
                "created_at": "2024-01-01T10:05:00Z",
                "updated_at": "2024-01-01T10:05:00Z"
            }
        ]
    },
    "intent_detail": {
        "summary": "意图详情响应示例",
        "value": {
            "id": 1,
            "intent_name": "greet",
            "description": "问候意图",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
            "utterances": [
                {
                    "id": 1,
                    "intent_id": 1,
                    "text": "你好",
                    "entities": None,
                    "created_at": "2024-01-01T10:00:00Z"
                },
                {
                    "id": 2,
                    "intent_id": 1,
                    "text": "您好",
                    "entities": None,
                    "created_at": "2024-01-01T10:00:00Z"
                }
            ],
            "responses": [
                {
                    "id": 1,
                    "intent_id": 1,
                    "type": "success",
                    "text": "您好！很高兴为您服务。",
                    "created_at": "2024-01-01T10:00:00Z"
                }
            ]
        }
    },
    "prediction": {
        "summary": "预测响应示例",
        "value": {
            "text": "你好",
            "intent": "greet",
            "confidence": 0.9876,
            "entities": [],
            "raw_rasa_response": {
                "intent": {
                    "name": "greet",
                    "confidence": 0.9876
                },
                "entities": [],
                "text": "你好"
            }
        }
    },
    "training_status": {
        "summary": "训练状态响应示例",
        "value": {
            "message": "训练任务已启动",
            "task_id": "training_20240101_100000",
            "model_version": "20240101-100000-model"
        }
    }
}
