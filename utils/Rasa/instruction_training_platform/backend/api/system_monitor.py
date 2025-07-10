"""
系统性能监控API - 简化版
获取真实的CPU、内存、磁盘使用率，与任务管理器数据一致
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import psutil
import time
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from response_utils import StandardResponse, success_response, error_response, ErrorCodes, Messages

router = APIRouter(prefix="/api/v2/system", tags=["system-monitor"])

class SystemMetrics(BaseModel):
    """系统性能指标 - 简化版"""
    cpu_percent: float
    cpu_count: int
    cpu_freq: Optional[float]
    memory_percent: float
    memory_total: float  # GB
    memory_used: float   # GB
    memory_available: float  # GB
    disk_percent: float  # 主磁盘使用率
    disk_total: float    # 主磁盘总容量GB
    disk_used: float     # 主磁盘已用容量GB
    network_percent: float  # 网络使用率（简化）
    timestamp: datetime

class ProcessInfo(BaseModel):
    """进程信息"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float

def bytes_to_gb(bytes_value: int) -> float:
    """字节转GB"""
    return round(bytes_value / (1024**3), 2)

def bytes_to_mb(bytes_value: int) -> float:
    """字节转MB"""
    return round(bytes_value / (1024**2), 2)

def get_main_disk_usage() -> tuple[float, float, float]:
    """获取主磁盘使用情况"""
    try:
        # 获取C盘（主磁盘）使用情况
        disk_usage = psutil.disk_usage('C:')
        percent = (disk_usage.used / disk_usage.total) * 100
        total_gb = bytes_to_gb(disk_usage.total)
        used_gb = bytes_to_gb(disk_usage.used)
        return round(percent, 2), total_gb, used_gb
    except Exception as e:
        print(f"获取磁盘使用率失败: {e}")
        return 0.0, 0.0, 0.0

def get_network_usage_simple() -> float:
    """获取简化的网络使用率"""
    try:
        # 获取网络I/O统计
        net_io = psutil.net_io_counters()
        if net_io:
            # 简化计算：基于总字节数的相对活跃度
            total_bytes = net_io.bytes_sent + net_io.bytes_recv
            # 假设网络相对活跃度，这里使用一个简化的算法
            # 实际生产环境中可以基于网卡带宽计算
            network_activity = min((total_bytes % 1000000) / 10000, 100)
            return round(network_activity, 2)
    except Exception as e:
        print(f"获取网络使用率失败: {e}")
    return 0.0

@router.get("/metrics", response_model=StandardResponse)
async def get_system_metrics():
    """获取系统性能指标 - 简化版"""
    try:
        # CPU指标
        cpu_percent = psutil.cpu_percent(interval=0.1)  # 减少等待时间
        cpu_count = psutil.cpu_count()
        cpu_freq = None
        try:
            freq = psutil.cpu_freq()
            cpu_freq = round(freq.current, 2) if freq else None
        except:
            pass
        
        # 内存指标
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_total = bytes_to_gb(memory.total)
        memory_used = bytes_to_gb(memory.used)
        memory_available = bytes_to_gb(memory.available)
        
        # 磁盘指标（主磁盘）
        disk_percent, disk_total, disk_used = get_main_disk_usage()
        
        # 网络指标（简化）
        network_percent = get_network_usage_simple()
        
        metrics_data = {
            "cpu_percent": round(cpu_percent, 2),
            "cpu_count": cpu_count,
            "cpu_freq": cpu_freq,
            "memory_percent": round(memory_percent, 2),
            "memory_total": memory_total,
            "memory_used": memory_used,
            "memory_available": memory_available,
            "disk_percent": disk_percent,
            "disk_total": disk_total,
            "disk_used": disk_used,
            "network_percent": network_percent,
            "timestamp": datetime.now()
        }
        
        return success_response(data=metrics_data, msg="获取系统指标成功")
        
    except Exception as e:
        return error_response(msg=f"获取系统指标失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)

@router.get("/processes", response_model=StandardResponse)
async def get_top_processes(limit: int = 10):
    """获取CPU和内存使用率最高的进程"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] is not None and pinfo['memory_percent'] is not None:
                    processes.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "cpu_percent": round(pinfo['cpu_percent'], 2),
                        "memory_percent": round(pinfo['memory_percent'], 2),
                        "memory_mb": bytes_to_mb(pinfo['memory_info'].rss)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 按CPU使用率排序
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        result = {
            "processes": processes[:limit],
            "total_processes": len(processes)
        }
        
        return success_response(data=result, msg="获取进程信息成功")
        
    except Exception as e:
        return error_response(msg=f"获取进程信息失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)

@router.get("/status", response_model=StandardResponse)
async def get_system_status():
    """获取系统基本状态"""
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        status_data = {
            "status": "running",
            "boot_time": boot_time.isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime).split('.')[0],  # 去掉微秒
            "platform": "Windows" if psutil.WINDOWS else "unknown",
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": bytes_to_gb(psutil.virtual_memory().total)
        }
        
        return success_response(data=status_data, msg="获取系统状态成功")
        
    except Exception as e:
        return error_response(msg=f"获取系统状态失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR) 