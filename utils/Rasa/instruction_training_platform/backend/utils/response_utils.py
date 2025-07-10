"""
统一API响应格式工具
提供标准化的API响应格式：code、msg、data
"""

from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class StandardResponse(BaseModel):
    """统一API响应格式"""
    code: str = Field(..., description="响应码，000000表示成功")
    msg: str = Field(..., description="响应消息，success表示成功")
    data: Optional[Any] = Field(None, description="响应数据")


# 成功响应辅助函数
def success_response(data: Any = None, msg: str = "success") -> StandardResponse:
    """
    生成成功响应
    
    Args:
        data: 响应数据
        msg: 响应消息，默认为"success"
        
    Returns:
        StandardResponse: 统一格式的成功响应
    """
    return StandardResponse(
        code="000000",
        msg=msg,
        data=data
    )


# 错误响应辅助函数
def error_response(msg: str, code: str = "999999", data: Any = None) -> StandardResponse:
    """
    生成错误响应
    
    Args:
        msg: 错误消息
        code: 错误码，默认为"999999"
        data: 额外的错误数据
        
    Returns:
        StandardResponse: 统一格式的错误响应
    """
    return StandardResponse(
        code=code,
        msg=msg,
        data=data
    )


# 常用错误码定义
class ErrorCodes:
    """常用错误码定义"""
    SUCCESS = "000000"              # 成功
    SYSTEM_ERROR = "999999"         # 系统错误
    PARAM_ERROR = "400001"          # 参数错误
    NOT_FOUND = "404001"            # 资源不存在
    ALREADY_EXISTS = "409001"       # 资源已存在
    UNAUTHORIZED = "401001"         # 未授权
    FORBIDDEN = "403001"            # 禁止访问
    VALIDATION_ERROR = "422001"     # 数据验证错误
    DATABASE_ERROR = "500001"       # 数据库错误
    EXTERNAL_API_ERROR = "500002"   # 外部API调用错误
    BUSINESS_ERROR = "400002"       # 业务逻辑错误


# 常用消息定义
class Messages:
    """常用响应消息定义"""
    SUCCESS = "success"
    SYSTEM_ERROR = "系统错误"
    PARAM_ERROR = "参数错误"
    NOT_FOUND = "资源不存在"
    ALREADY_EXISTS = "资源已存在"
    UNAUTHORIZED = "未授权访问"
    FORBIDDEN = "禁止访问"
    VALIDATION_ERROR = "数据验证失败"
    DATABASE_ERROR = "数据库操作失败"
    EXTERNAL_API_ERROR = "外部API调用失败"


# 分页响应格式
class PaginatedData(BaseModel):
    """分页数据格式"""
    items: list = Field(..., description="数据列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


def paginated_success_response(
    items: list, 
    total: int, 
    page: int, 
    size: int, 
    msg: str = "success"
) -> StandardResponse:
    """
    生成分页成功响应
    
    Args:
        items: 数据列表
        total: 总数量
        page: 当前页码
        size: 每页大小
        msg: 响应消息
        
    Returns:
        StandardResponse: 统一格式的分页响应
    """
    pages = (total + size - 1) // size if size > 0 else 0
    
    paginated_data = PaginatedData(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )
    
    return success_response(data=paginated_data.dict(), msg=msg) 