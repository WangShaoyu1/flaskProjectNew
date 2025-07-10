#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志中间件
自动记录所有API请求和响应
"""

import time
import json
from typing import Callable
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import asyncio

from utils.logger import log_api_request, log_error, log_system

class ConsoleLoggingMiddleware(BaseHTTPMiddleware):
    """控制台日志中间件 - 显示详细的API请求信息"""
    
    def __init__(self, app, skip_paths: list = None):
        super().__init__(app)
        # 跳过记录的路径
        self.skip_paths = skip_paths or [
            "/favicon.ico",
            "/static",
            "/openapi.json"
        ]
        
        # 颜色代码
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'magenta': '\033[35m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'gray': '\033[90m'
        }
    
    def colorize(self, text: str, color: str) -> str:
        """给文本添加颜色"""
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"
    
    def get_status_color(self, status_code: int) -> str:
        """根据状态码获取颜色"""
        if status_code >= 500:
            return 'red'
        elif status_code >= 400:
            return 'yellow'
        elif status_code >= 300:
            return 'cyan'
        else:
            return 'green'
    
    def get_method_color(self, method: str) -> str:
        """根据HTTP方法获取颜色"""
        colors = {
            'GET': 'green',
            'POST': 'blue',
            'PUT': 'yellow',
            'DELETE': 'red',
            'PATCH': 'magenta',
            'HEAD': 'gray',
            'OPTIONS': 'gray'
        }
        return colors.get(method.upper(), 'white')
    
    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        url = str(request.url)
        path = request.url.path
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 检查是否跳过记录
        should_skip = any(skip_path in path for skip_path in self.skip_paths)
        
        # 获取请求大小
        content_length = request.headers.get("content-length")
        request_size = int(content_length) if content_length else 0
        
        # 处理请求
        error_occurred = False
        try:
            response = await call_next(request)
        except Exception as e:
            error_occurred = True
            # 创建错误响应
            from fastapi import HTTPException
            from fastapi.responses import JSONResponse
            
            if isinstance(e, HTTPException):
                response = JSONResponse(
                    status_code=e.status_code,
                    content={"error": e.detail}
                )
            else:
                response = JSONResponse(
                    status_code=500,
                    content={"error": "Internal Server Error"}
                )
        
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 获取响应大小
        response_size = 0
        if hasattr(response, 'headers') and 'content-length' in response.headers:
            response_size = int(response.headers['content-length'])
        
        # 在控制台显示请求信息（除非在跳过列表中）
        if not should_skip:
            self.print_request_info(
                method, path, response.status_code, response_time,
                client_ip, request_size, response_size, error_occurred
            )
        
        return response
    
    def print_request_info(self, method: str, path: str, status_code: int, 
                          response_time: float, client_ip: str, 
                          request_size: int, response_size: int, error_occurred: bool):
        """在控制台打印请求信息"""
        
        # 格式化时间
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 格式化响应时间
        if response_time < 0.001:
            time_str = f"{response_time * 1000000:.0f}μs"
        elif response_time < 1:
            time_str = f"{response_time * 1000:.0f}ms"
        else:
            time_str = f"{response_time:.2f}s"
        
        # 选择颜色
        method_color = self.get_method_color(method)
        status_color = self.get_status_color(status_code)
        
        # 构建日志行
        log_parts = [
            self.colorize(f"[{timestamp}]", 'gray'),
            self.colorize(f"{method:>6}", method_color),
            self.colorize(f"{status_code}", status_color),
            self.colorize(f"{time_str:>8}", 'cyan'),
            path
        ]
        
        # 添加客户端IP（如果不是本地）
        if client_ip and client_ip not in ['127.0.0.1', 'localhost', '::1']:
            log_parts.append(self.colorize(f"({client_ip})", 'gray'))
        
        # 添加大小信息
        if request_size > 0 or response_size > 0:
            size_info = []
            if request_size > 0:
                size_info.append(f"↑{self.format_size(request_size)}")
            if response_size > 0:
                size_info.append(f"↓{self.format_size(response_size)}")
            if size_info:
                log_parts.append(self.colorize(f"[{'/'.join(size_info)}]", 'gray'))
        
        # 添加错误标识
        if error_occurred:
            log_parts.append(self.colorize("❌", 'red'))
        
        # 打印日志
        print(" ".join(log_parts))
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 优先获取代理头中的IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 获取直接连接的IP
        if request.client:
            return request.client.host
        
        return "unknown"

class LoggingMiddleware(BaseHTTPMiddleware):
    """API请求日志中间件 - 记录到文件"""
    
    def __init__(self, app, skip_paths: list = None):
        super().__init__(app)
        # 跳过记录的路径（如健康检查、静态文件等）
        self.skip_paths = skip_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/favicon.ico",
            "/static"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        url = str(request.url)
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 检查是否跳过记录
        should_skip = any(skip_path in url for skip_path in self.skip_paths)
        
        # 读取请求体（如果存在）
        request_body = None
        if not should_skip and method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # 尝试解析JSON
                    try:
                        request_body = json.loads(body.decode('utf-8'))
                    except:
                        request_body = body.decode('utf-8', errors='ignore')
            except Exception as e:
                log_error(f"读取请求体失败: {str(e)}")
        
        # 处理请求
        error_message = None
        response_body = None
        
        try:
            response = await call_next(request)
            
            # 记录响应体（仅在调试模式下）
            if not should_skip and hasattr(response, 'body'):
                try:
                    if isinstance(response, StreamingResponse):
                        # 对于流式响应，不记录响应体
                        pass
                    else:
                        # 尝试获取响应体
                        body = getattr(response, 'body', None)
                        if body:
                            try:
                                response_body = json.loads(body.decode('utf-8'))
                            except:
                                response_body = body.decode('utf-8', errors='ignore')
                except Exception as e:
                    log_error(f"读取响应体失败: {str(e)}")
            
        except Exception as e:
            # 记录异常
            error_message = str(e)
            log_error(f"请求处理异常: {method} {url}", error=e, extra_data={
                "client_ip": client_ip,
                "user_agent": user_agent,
                "request_body": request_body
            })
            
            # 创建错误响应
            from fastapi import HTTPException
            from fastapi.responses import JSONResponse
            
            if isinstance(e, HTTPException):
                response = JSONResponse(
                    status_code=e.status_code,
                    content={"error": e.detail}
                )
            else:
                response = JSONResponse(
                    status_code=500,
                    content={"error": "Internal Server Error"}
                )
        
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 记录API请求日志（除非在跳过列表中）
        if not should_skip:
            log_api_request(
                method=method,
                url=url,
                status_code=response.status_code,
                response_time=response_time,
                client_ip=client_ip,
                user_agent=user_agent,
                request_body=request_body,
                response_body=response_body,
                error=error_message
            )
        
        # 添加响应头
        response.headers["X-Response-Time"] = f"{response_time:.3f}s"
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 优先获取代理头中的IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 获取直接连接的IP
        if request.client:
            return request.client.host
        
        return "unknown"

class SystemEventLogger:
    """系统事件日志记录器"""
    
    @staticmethod
    def log_startup():
        """记录系统启动"""
        log_system("系统启动", level="info", extra_data={
            "event": "startup",
            "version": "2.0.0"
        })
    
    @staticmethod
    def log_shutdown():
        """记录系统关闭"""
        log_system("系统关闭", level="info", extra_data={
            "event": "shutdown"
        })
    
    @staticmethod
    def log_database_init():
        """记录数据库初始化"""
        log_system("数据库初始化完成", level="info", extra_data={
            "event": "database_init"
        })
    
    @staticmethod
    def log_database_error(error: Exception):
        """记录数据库错误"""
        log_error("数据库初始化失败", error=error, extra_data={
            "event": "database_error"
        }) 