#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志查看API
提供查看系统日志的接口
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
import os
import json
from datetime import datetime, timedelta
from utils.response_utils import StandardResponse, success_response, error_response, ErrorCodes

router = APIRouter(prefix="/api/v2/logs", tags=["日志查看"])

def get_logs_dir():
    """获取日志目录的绝对路径"""
    # 获取当前文件所在目录的上级目录（backend）
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(backend_dir, "logs")

@router.get("/list", response_model=StandardResponse)
async def get_log_files():
    """获取可用的日志文件列表"""
    try:
        logs_dir = get_logs_dir()
        if not os.path.exists(logs_dir):
            return success_response(data=[], msg="日志目录不存在")
        
        log_files = []
        for filename in os.listdir(logs_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(logs_dir, filename)
                file_stat = os.stat(filepath)
                
                log_files.append({
                    "filename": filename,
                    "size": file_stat.st_size,
                    "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                    "modified_time": datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    "description": get_log_description(filename)
                })
        
        # 按修改时间排序
        log_files.sort(key=lambda x: x['modified_time'], reverse=True)
        
        return success_response(data=log_files, msg="获取日志文件列表成功")
        
    except Exception as e:
        return error_response(msg=f"获取日志文件列表失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)

@router.get("/view/{log_file}", response_model=StandardResponse)
async def view_log_file(
    log_file: str,
    lines: int = Query(100, ge=1, le=1000, description="读取行数"),
    from_end: bool = Query(True, description="从文件末尾开始读取"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """查看日志文件内容"""
    try:
        # 安全检查，防止路径遍历
        if '..' in log_file or '/' in log_file or '\\' in log_file:
            return error_response(msg="非法的文件名", code=ErrorCodes.VALIDATION_ERROR)
        
        logs_dir = get_logs_dir()
        filepath = os.path.join(logs_dir, log_file)
        
        if not os.path.exists(filepath):
            return error_response(msg="日志文件不存在", code=ErrorCodes.NOT_FOUND)
        
        # 读取文件内容
        with open(filepath, 'r', encoding='utf-8') as f:
            if from_end:
                # 从末尾读取指定行数
                all_lines = f.readlines()
                log_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            else:
                # 从开头读取指定行数
                log_lines = []
                for i, line in enumerate(f):
                    if i >= lines:
                        break
                    log_lines.append(line)
        
        # 如果有搜索关键词，过滤日志
        if search:
            log_lines = [line for line in log_lines if search.lower() in line.lower()]
        
        # 处理日志行
        processed_lines = []
        for line in log_lines:
            line = line.strip()
            if line:
                processed_lines.append(line)
        
        return success_response(data={
            "filename": log_file,
            "lines": processed_lines,
            "total_lines": len(processed_lines),
            "from_end": from_end,
            "search": search
        }, msg="读取日志文件成功")
        
    except Exception as e:
        return error_response(msg=f"读取日志文件失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)

@router.get("/search", response_model=StandardResponse)
async def search_logs(
    keyword: str = Query(..., description="搜索关键词"),
    log_files: Optional[List[str]] = Query(None, description="指定搜索的日志文件"),
    max_results: int = Query(100, ge=1, le=500, description="最大结果数"),
    date_from: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)")
):
    """搜索日志内容"""
    try:
        logs_dir = get_logs_dir()
        if not os.path.exists(logs_dir):
            return success_response(data=[], msg="日志目录不存在")
        
        # 确定要搜索的文件
        if log_files:
            files_to_search = log_files
        else:
            files_to_search = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
        
        search_results = []
        
        for filename in files_to_search:
            filepath = os.path.join(logs_dir, filename)
            if not os.path.exists(filepath):
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if keyword.lower() in line.lower():
                            # 检查日期范围
                            if date_from or date_to:
                                line_date = extract_date_from_log_line(line)
                                if line_date:
                                    if date_from and line_date < date_from:
                                        continue
                                    if date_to and line_date > date_to:
                                        continue
                            
                            search_results.append({
                                "filename": filename,
                                "line_number": line_num,
                                "content": line.strip(),
                                "timestamp": extract_timestamp_from_log_line(line)
                            })
                            
                            if len(search_results) >= max_results:
                                break
                
                if len(search_results) >= max_results:
                    break
                    
            except Exception as e:
                continue
        
        return success_response(data={
            "keyword": keyword,
            "results": search_results,
            "total_found": len(search_results),
            "searched_files": files_to_search
        }, msg="搜索日志完成")
        
    except Exception as e:
        return error_response(msg=f"搜索日志失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)

@router.get("/stats", response_model=StandardResponse)
async def get_log_stats():
    """获取日志统计信息"""
    try:
        logs_dir = get_logs_dir()
        if not os.path.exists(logs_dir):
            return success_response(data={}, msg="日志目录不存在")
        
        stats = {
            "total_files": 0,
            "total_size": 0,
            "files": []
        }
        
        for filename in os.listdir(logs_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(logs_dir, filename)
                file_stat = os.stat(filepath)
                
                # 计算文件行数
                line_count = 0
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                except:
                    line_count = 0
                
                file_info = {
                    "filename": filename,
                    "size": file_stat.st_size,
                    "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                    "lines": line_count,
                    "modified_time": datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    "description": get_log_description(filename)
                }
                
                stats["files"].append(file_info)
                stats["total_files"] += 1
                stats["total_size"] += file_stat.st_size
        
        stats["total_size_mb"] = round(stats["total_size"] / (1024 * 1024), 2)
        
        return success_response(data=stats, msg="获取日志统计信息成功")
        
    except Exception as e:
        return error_response(msg=f"获取日志统计信息失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)

def get_log_description(filename: str) -> str:
    """获取日志文件描述"""
    descriptions = {
        "api_requests.log": "API请求日志",
        "system.log": "系统运行日志",
        "errors.log": "错误日志",
        "database.log": "数据库操作日志",
        "training.log": "模型训练日志"
    }
    return descriptions.get(filename, "未知日志文件")

def extract_timestamp_from_log_line(line: str) -> Optional[str]:
    """从日志行中提取时间戳"""
    try:
        # 假设日志格式是 [2024-01-01 12:00:00.123] ...
        if line.startswith('[') and ']' in line:
            timestamp_part = line.split(']')[0][1:]
            return timestamp_part
    except:
        pass
    return None

def extract_date_from_log_line(line: str) -> Optional[str]:
    """从日志行中提取日期"""
    try:
        timestamp = extract_timestamp_from_log_line(line)
        if timestamp:
            # 提取日期部分
            return timestamp.split(' ')[0]
    except:
        pass
    return None 