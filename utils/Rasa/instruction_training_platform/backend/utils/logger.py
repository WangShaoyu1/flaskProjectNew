#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志配置模块
提供统一的日志记录功能
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
from typing import Any, Dict, Optional
import traceback

class CustomFormatter(logging.Formatter):
    """自定义日志格式化器"""
    
    def format(self, record):
        # 添加时间戳
        record.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # 如果有额外的数据，格式化为JSON
        if hasattr(record, 'extra_data') and record.extra_data:
            record.extra_data_str = json.dumps(record.extra_data, ensure_ascii=False, indent=2)
        else:
            record.extra_data_str = ""
        
        return super().format(record)

class APILogger:
    """API日志记录器"""
    
    def __init__(self, logs_dir: str = "logs"):
        # 确保使用绝对路径
        if not os.path.isabs(logs_dir):
            # 获取当前文件所在目录的上级目录（backend）
            backend_dir = os.path.dirname(os.path.dirname(__file__))
            logs_dir = os.path.join(backend_dir, logs_dir)
        self.logs_dir = logs_dir
        self.ensure_logs_dir()
        self.setup_loggers()
    
    def ensure_logs_dir(self):
        """确保日志目录存在"""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
    
    def setup_loggers(self):
        """设置日志记录器"""
        
        # 创建自定义格式化器
        formatter = CustomFormatter(
            fmt='[%(timestamp)s] [%(levelname)s] [%(name)s] %(message)s%(extra_data_str)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 1. API请求日志
        self.api_logger = logging.getLogger('api_requests')
        self.api_logger.setLevel(logging.INFO)
        api_handler = TimedRotatingFileHandler(
            filename=os.path.join(self.logs_dir, 'api_requests.log'),
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        api_handler.setFormatter(formatter)
        self.api_logger.addHandler(api_handler)
        
        # 2. 系统日志
        self.system_logger = logging.getLogger('system')
        self.system_logger.setLevel(logging.INFO)
        system_handler = TimedRotatingFileHandler(
            filename=os.path.join(self.logs_dir, 'system.log'),
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        system_handler.setFormatter(formatter)
        self.system_logger.addHandler(system_handler)
        
        # 3. 错误日志
        self.error_logger = logging.getLogger('errors')
        self.error_logger.setLevel(logging.ERROR)
        error_handler = TimedRotatingFileHandler(
            filename=os.path.join(self.logs_dir, 'errors.log'),
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setFormatter(formatter)
        self.error_logger.addHandler(error_handler)
        
        # 4. 数据库操作日志
        self.db_logger = logging.getLogger('database')
        self.db_logger.setLevel(logging.INFO)
        db_handler = TimedRotatingFileHandler(
            filename=os.path.join(self.logs_dir, 'database.log'),
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        db_handler.setFormatter(formatter)
        self.db_logger.addHandler(db_handler)
        
        # 5. 训练日志
        self.training_logger = logging.getLogger('training')
        self.training_logger.setLevel(logging.INFO)
        training_handler = TimedRotatingFileHandler(
            filename=os.path.join(self.logs_dir, 'training.log'),
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        training_handler.setFormatter(formatter)
        self.training_logger.addHandler(training_handler)
        
        # 阻止日志传播到根记录器
        for logger in [self.api_logger, self.system_logger, self.error_logger, 
                      self.db_logger, self.training_logger]:
            logger.propagate = False
    
    def log_api_request(self, method: str, url: str, status_code: int, 
                       response_time: float, client_ip: str = None, 
                       user_agent: str = None, request_body: Any = None,
                       response_body: Any = None, error: str = None):
        """记录API请求日志"""
        
        extra_data = {
            "method": method,
            "url": url,
            "status_code": status_code,
            "response_time_ms": round(response_time * 1000, 2),
            "client_ip": client_ip,
            "user_agent": user_agent,
        }
        
        # 只在调试模式下记录请求体和响应体
        if os.getenv('DEBUG', 'false').lower() == 'true':
            if request_body:
                extra_data["request_body"] = request_body
            if response_body:
                extra_data["response_body"] = response_body
        
        if error:
            extra_data["error"] = error
        
        message = f"{method} {url} - {status_code} - {response_time*1000:.2f}ms"
        
        if status_code >= 500:
            self.api_logger.error(message, extra={'extra_data': extra_data})
        elif status_code >= 400:
            self.api_logger.warning(message, extra={'extra_data': extra_data})
        else:
            self.api_logger.info(message, extra={'extra_data': extra_data})
    
    def log_system(self, message: str, level: str = 'info', extra_data: Dict = None):
        """记录系统日志"""
        log_func = getattr(self.system_logger, level.lower(), self.system_logger.info)
        log_func(message, extra={'extra_data': extra_data or {}})
    
    def log_error(self, message: str, error: Exception = None, extra_data: Dict = None):
        """记录错误日志"""
        if error:
            error_info = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            }
            if extra_data:
                error_info.update(extra_data)
            extra_data = error_info
        
        self.error_logger.error(message, extra={'extra_data': extra_data or {}})
    
    def log_database(self, operation: str, table: str = None, 
                    record_id: Any = None, extra_data: Dict = None):
        """记录数据库操作日志"""
        data = {
            "operation": operation,
            "table": table,
            "record_id": record_id,
        }
        if extra_data:
            data.update(extra_data)
        
        message = f"数据库操作: {operation}"
        if table:
            message += f" - 表: {table}"
        if record_id:
            message += f" - ID: {record_id}"
        
        self.db_logger.info(message, extra={'extra_data': data})
    
    def log_training(self, message: str, level: str = 'info', 
                    library_id: int = None, version: int = None, 
                    extra_data: Dict = None):
        """记录训练日志"""
        data = {
            "library_id": library_id,
            "version": version,
        }
        if extra_data:
            data.update(extra_data)
        
        log_func = getattr(self.training_logger, level.lower(), self.training_logger.info)
        log_func(message, extra={'extra_data': data})

# 创建全局日志实例
logger_instance = APILogger()

# 导出便捷函数
def log_api_request(*args, **kwargs):
    """记录API请求"""
    return logger_instance.log_api_request(*args, **kwargs)

def log_system(*args, **kwargs):
    """记录系统日志"""
    return logger_instance.log_system(*args, **kwargs)

def log_error(*args, **kwargs):
    """记录错误日志"""
    return logger_instance.log_error(*args, **kwargs)

def log_database(*args, **kwargs):
    """记录数据库操作"""
    return logger_instance.log_database(*args, **kwargs)

def log_training(*args, **kwargs):
    """记录训练日志"""
    return logger_instance.log_training(*args, **kwargs)

# 获取特定的日志记录器
def get_logger(name: str):
    """获取指定名称的日志记录器"""
    loggers = {
        'api': logger_instance.api_logger,
        'system': logger_instance.system_logger,
        'error': logger_instance.error_logger,
        'database': logger_instance.db_logger,
        'training': logger_instance.training_logger,
    }
    return loggers.get(name, logger_instance.system_logger)

def setup_logger(name: str):
    """设置日志记录器（兼容性函数）"""
    return get_logger(name) 