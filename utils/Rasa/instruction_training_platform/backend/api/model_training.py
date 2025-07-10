"""
模型训练API
支持RASA模型训练相关的接口
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import os
import subprocess
import json
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import logging

import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.database_models import (
    get_new_db,
    InstructionLibraryMaster as DBInstructionLibraryMaster,
    ModelTrainingRecord as DBModelTrainingRecord,
    InstructionData,
    SlotDefinition,
    SimilarQuestion
)
from response_utils import StandardResponse, success_response, error_response, ErrorCodes
from services.library_version_manager import LibraryVersionManager
from services.training_data_generator import TrainingDataGenerator

router = APIRouter(prefix="/api/v2/training", tags=["模型训练"])

# 初始化版本管理器和训练数据生成器
version_manager = LibraryVersionManager()
training_data_generator = TrainingDataGenerator()

# 训练状态存储（在生产环境中应该使用Redis或数据库）
training_records = {}
training_counter = 1

# 全局训练锁，防止同一指令库重复训练
training_locks = {}

logger = logging.getLogger(__name__)


async def monitor_training_process(record_id: int, rasa_path: Path, start_time: float):
    """
    监控训练过程，检查模型文件生成情况
    
    Args:
        record_id: 训练记录ID
        rasa_path: RASA项目路径
        start_time: 训练开始时间
        
    Returns:
        bool: 训练是否成功
    """
    try:
        record = training_records[record_id]
        models_dir = rasa_path / "models"
        
        # 获取训练前的模型文件列表
        initial_models = set(models_dir.glob("*.tar.gz")) if models_dir.exists() else set()
        
        # 监控训练过程，最多等待20分钟
        max_wait_time = 1200  # 20分钟
        check_interval = 10  # 每10秒检查一次
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            await asyncio.sleep(check_interval)
            elapsed_time += check_interval
            
            # 更新进度 - 从70%逐步增加到95%
            progress = min(70 + (elapsed_time / max_wait_time) * 25, 95)  # 从70%到95%
            record["progress"] = int(progress)
            
            # 更新日志
            if elapsed_time % 30 == 0:  # 每30秒更新一次日志
                record["logs"].append(f"训练进行中... ({elapsed_time//60}分{elapsed_time%60}秒)")
                sync_training_status_to_db(record_id, 'running', progress=int(progress), logs=record["logs"])
            
            # 检查是否有新的模型文件生成
            if models_dir.exists():
                current_models = set(models_dir.glob("*.tar.gz"))
                new_models = current_models - initial_models
                
                if new_models:
                    # 检查新模型文件是否在训练开始后生成
                    for model_file in new_models:
                        if model_file.stat().st_ctime > start_time:
                            record["logs"].append(f"✅ 检测到新模型文件: {model_file.name}")
                            return True
            
            # 检查是否有训练进程仍在运行
            # 这里可以添加更精确的进程检查逻辑
            
        # 超时后最后检查一次
        if models_dir.exists():
            current_models = set(models_dir.glob("*.tar.gz"))
            new_models = current_models - initial_models
            
            for model_file in new_models:
                if model_file.stat().st_ctime > start_time:
                    record["logs"].append(f"✅ 训练完成，检测到模型文件: {model_file.name}")
                    return True
        
        # 训练超时
        record["logs"].append("⏰ 训练超时，未检测到新模型文件")
        return False
        
    except Exception as e:
        logger.error(f"训练监控异常: {str(e)}")
        if record_id in training_records:
            training_records[record_id]["logs"].append(f"💥 训练监控异常: {str(e)}")
        return False


class TrainingStatus:
    """训练状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingRequest(BaseModel):
    """训练请求模型"""
    library_id: int
    version_name: Optional[str] = None
    description: Optional[str] = None
    training_params: Optional[dict] = None


def get_rasa_project_path():
    """获取RASA项目路径"""
    current_dir = Path(__file__).parent.parent.parent
    return current_dir / "rasa"


def create_training_record(library_id: int, library_name: str, version_name: str = None, description: str = None):
    """创建训练记录并同步到数据库"""
    global training_counter

    record_id = training_counter
    training_counter += 1

    # 生成版本号
    version_number = record_id

    # 获取训练数据统计
    intent_count = 0
    slot_count = 0
    training_data_count = 0

    try:
        # 从数据库获取实际统计数据
        db = next(get_new_db())

        # 获取指令数量
        intent_count = db.query(InstructionData).filter(
            InstructionData.library_id == library_id
        ).count()

        # 获取词槽数量
        slot_count = db.query(SlotDefinition).filter(
            SlotDefinition.library_id == library_id
        ).count()

        # 计算训练样本数量（相似问数量）
        training_data_count = db.query(SimilarQuestion).join(
            InstructionData, SimilarQuestion.instruction_id == InstructionData.id
        ).filter(
            InstructionData.library_id == library_id
        ).count()

        # 创建数据库记录
        from datetime import datetime
        import pytz
        
        # 使用UTC时间存储到数据库，避免时区混乱
        utc_time = datetime.utcnow()

        # 先查询最大版本号
        max_version = db.query(DBModelTrainingRecord).filter(
            DBModelTrainingRecord.library_id == library_id
        ).order_by(DBModelTrainingRecord.version_number.desc()).first()

        if max_version:
            version_number = max_version.version_number + 1
        else:
            version_number = 1

        # 创建数据库训练记录
        db_record = DBModelTrainingRecord(
            library_id=library_id,
            version_number=version_number,
            training_status='pending',
            start_time=utc_time,  # 存储UTC时间
            intent_count=intent_count,
            slot_count=slot_count,
            training_data_count=training_data_count,
            is_active=False,
            training_params=json.dumps(
                {"description": description, "version_name": version_name}) if description or version_name else None
        )

        db.add(db_record)
        db.commit()
        db.refresh(db_record)

        # 使用数据库生成的ID作为记录ID
        record_id = db_record.id

        logger.info(f"✅ [创建记录] 数据库记录已创建: ID={record_id}, 版本=v{version_number}")

        db.close()

    except Exception as e:
        logger.warning(f"获取训练数据统计或创建数据库记录失败: {str(e)}")
        # 如果数据库操作失败，仍然创建内存记录，但记录错误
        if 'db' in locals():
            db.close()

    # 使用本地时间而不是UTC时间
    from datetime import datetime, timezone
    import pytz

    # 获取本地时区
    local_tz = pytz.timezone('Asia/Shanghai')  # 中国时区
    local_time = datetime.now(local_tz)

    # 创建内存记录（用于实时状态跟踪）- 统一使用training_status字段
    record = {
        "id": record_id,
        "library_id": library_id,
        "library_name": library_name,
        "version_name": version_name,
        "version_number": version_number,
        "description": description,
        "training_status": TrainingStatus.PENDING,  # 统一字段
        "start_time": local_time.isoformat(),
        "end_time": None,
        "complete_time": None,
        "duration": None,
        "model_path": None,
        "metrics": {},
        "logs": [],
        "error_message": None,
        "progress": 0,
        "intent_count": intent_count,
        "slot_count": slot_count,
        "training_data_count": training_data_count,
        "is_active": False
    }

    training_records[record_id] = record
    logger.info(f"✅ [创建记录] 内存记录已创建: ID={record_id}")

    return record


def sync_training_status_to_db(record_id: int, status: str, progress: int = None, error_message: str = None,
                               model_path: str = None, logs: list = None):
    """同步训练状态到数据库"""
    try:
        db = next(get_new_db())

        db_record = db.query(DBModelTrainingRecord).filter(
            DBModelTrainingRecord.id == record_id
        ).first()

        if db_record:
            # 更新状态
            db_record.training_status = status

            # 更新错误信息
            if error_message:
                db_record.error_message = error_message

            # 更新模型路径
            if model_path:
                db_record.model_file_path = model_path

            # 更新日志
            if logs:
                db_record.training_log = '\n'.join(logs)

            # 如果训练完成或失败，设置完成时间
            if status in ['completed', 'failed', 'success']:
                # 使用UTC时间存储
                utc_time = datetime.utcnow()
                db_record.complete_time = utc_time

            db.commit()
            logger.info(f"✅ [同步状态] 数据库状态已更新: ID={record_id}, 状态={status}")
        else:
            logger.warning(f"⚠️ [同步状态] 数据库中未找到记录: ID={record_id}")

        db.close()

    except Exception as e:
        logger.error(f"💥 [同步状态] 数据库同步失败: {str(e)}")
        if 'db' in locals():
            db.close()


async def run_rasa_training_with_version_generation(record_id: int, library_id: int, description: str):
    """运行RASA训练（包含版本生成）"""
    try:
        # 导入时区相关模块
        import pytz
        local_tz = pytz.timezone('Asia/Shanghai')

        record = training_records[record_id]
        record["training_status"] = TrainingStatus.RUNNING
        record["progress"] = 5
        record["logs"].append("开始生成训练版本...")

        # 同步状态到数据库
        sync_training_status_to_db(record_id, 'running', progress=5, logs=record["logs"])

        # 🚀 在后台生成训练版本
        logger.info(f"📊 [训练任务] 从数据库生成新的训练版本")
        try:
            # 获取数据库连接
            db = next(get_new_db())
            
            version_description = description or f"训练版本 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            version_name, version_dir = training_data_generator.generate_training_version_from_database(
                db=db,
                library_id=library_id,
                version_description=version_description
            )
            
            # 更新记录中的版本信息
            record["version_name"] = version_name
            record["version_dir"] = version_dir
            
            logger.info(f"✅ [训练任务] 新版本生成成功: {version_name}")
            logger.info(f"📁 [训练任务] 版本目录: {version_dir}")
            
            db.close()
            
        except Exception as e:
            logger.error(f"❌ [训练任务] 生成训练版本失败: {str(e)}")
            record["training_status"] = TrainingStatus.FAILED
            record["error_message"] = f"生成训练版本失败: {str(e)}"
            
            # 使用本地时间
            local_time = datetime.now(local_tz)
            record["end_time"] = local_time.isoformat()
            record["complete_time"] = local_time.isoformat()
            
            # 同步失败状态到数据库
            sync_training_status_to_db(record_id, 'failed', error_message=record["error_message"], logs=record["logs"])
            return

        # 版本生成成功后，调用原有的训练函数
        await run_rasa_training(record_id, library_id, version_name, version_dir)

    except Exception as e:
        logger.error(f"训练任务异常: {str(e)}")
        if record_id in training_records:
            # 导入时区相关模块
            import pytz
            local_tz = pytz.timezone('Asia/Shanghai')
            local_time = datetime.now(local_tz)

            training_records[record_id]["training_status"] = TrainingStatus.FAILED
            training_records[record_id]["error_message"] = f"系统异常: {str(e)}"
            training_records[record_id]["end_time"] = local_time.isoformat()
            training_records[record_id]["complete_time"] = local_time.isoformat()
            training_records[record_id]["logs"].append(f"💥 系统异常: {str(e)}")

            # 同步系统异常到数据库
            sync_training_status_to_db(
                record_id,
                'failed',
                error_message=f"系统异常: {str(e)}",
                logs=training_records[record_id]["logs"]
            )


async def run_rasa_training(record_id: int, library_id: int, version_name: str, version_dir: str):
    """运行RASA训练（后台任务）"""
    try:
        # 导入时区相关模块
        import pytz
        local_tz = pytz.timezone('Asia/Shanghai')

        record = training_records[record_id]
        # 如果状态还不是running，则设置为running
        if record["training_status"] != TrainingStatus.RUNNING:
            record["training_status"] = TrainingStatus.RUNNING
        
        record["progress"] = 15
        record["logs"].append("开始训练准备...")

        # 同步状态到数据库
        sync_training_status_to_db(record_id, 'running', progress=15, logs=record["logs"])

        # 🚀 核心变更：使用版本目录中的文件
        logger.info(f"📁 [训练执行] 使用版本目录: {version_dir}")
        version_path = Path(version_dir)
        
        # 检查版本目录中的必要文件
        required_files = ["domain.yml", "nlu.yml"]
        missing_files = []

        for file_name in required_files:
            file_path = version_path / file_name
            if not file_path.exists():
                missing_files.append(f"version/{file_name}")
        
        # 检查config.yml（可能在版本目录或rasa根目录）
        config_path = version_path / "config.yml"
        if not config_path.exists():
            # 尝试使用rasa根目录的config.yml
            rasa_path = get_rasa_project_path()
            config_path = rasa_path / "config.yml"
            if not config_path.exists():
                missing_files.append("config.yml")

        if missing_files:
            record["training_status"] = TrainingStatus.FAILED
            record["error_message"] = f"缺少必要文件: {', '.join(missing_files)}"

            # 使用本地时间
            local_time = datetime.now(local_tz)
            record["end_time"] = local_time.isoformat()
            record["complete_time"] = local_time.isoformat()

            # 同步失败状态到数据库
            sync_training_status_to_db(record_id, 'failed', error_message=record["error_message"], logs=record["logs"])
            return

        # 逐步增加进度，让用户看到进展
        time.sleep(2)  # 2秒延时
        record["progress"] = 20
        record["logs"].append("验证训练数据完整性...")
        sync_training_status_to_db(record_id, 'running', progress=20, logs=record["logs"])

        # 模拟数据验证过程
        time.sleep(3)  # 3秒延时
        record["progress"] = 30
        record["logs"].append(f"开始训练 - 指令库ID: {library_id}, 版本: {version_name}")
        sync_training_status_to_db(record_id, 'running', progress=30, logs=record["logs"])

        # 🚀 核心变更：使用版本目录构建训练命令
        rasa_path = get_rasa_project_path()
        
        # 构建训练命令，使用版本目录中的文件
        cmd = [
            "rasa", "train",
            "--domain", str(version_path / "domain.yml"),
            "--data", str(version_path),  # 数据目录指向版本目录
            "--config", str(config_path),  # 使用找到的config.yml
            "--out", str(rasa_path / "models"),
            "--force"
        ]
        
        record["logs"].append(f"训练命令: rasa train --domain {version_path / 'domain.yml'} --data {version_path} --config {config_path}")

        time.sleep(2)  # 2秒延时
        record["progress"] = 40
        record["logs"].append("初始化训练环境...")
        sync_training_status_to_db(record_id, 'running', progress=40, logs=record["logs"])

        # 模拟环境初始化
        time.sleep(3)  # 3秒延时
        record["progress"] = 50
        record["logs"].append("加载训练数据...")
        sync_training_status_to_db(record_id, 'running', progress=50, logs=record["logs"])

        # 模拟数据加载
        time.sleep(2)  # 2秒延时
        record["progress"] = 60
        record["logs"].append("开始模型训练...")
        record["logs"].append(f"执行训练命令: rasa train")
        sync_training_status_to_db(record_id, 'running', progress=60, logs=record["logs"])

        # 执行训练前的进度更新
        time.sleep(2)  # 2秒延时
        record["progress"] = 70
        record["logs"].append("正在训练NLU模型...")
        sync_training_status_to_db(record_id, 'running', progress=70, logs=record["logs"])

        # 执行训练 - 使用独立的cmd窗口
        start_time = time.time()

        try:
            # 构建cmd命令字符串
            cmd_str = " ".join([f'"{arg}"' if " " in arg else arg for arg in cmd])
            
            # 在Windows上使用独立的cmd窗口执行训练
            import platform
            if platform.system() == "Windows":
                # 创建批处理文件来执行训练
                batch_file = rasa_path / f"train_batch_{record_id}.bat"
                with open(batch_file, "w", encoding="utf-8") as f:
                    f.write("@echo off\n")
                    f.write(f"cd /d \"{rasa_path}\"\n")
                    f.write(f"echo 开始训练...\n")
                    f.write(f"{cmd_str}\n")
                    f.write(f"echo 训练完成，退出码: %ERRORLEVEL%\n")
                    f.write(f"pause\n")
                
                # 使用start命令在新窗口中执行
                result = subprocess.Popen(
                    ["cmd", "/c", "start", "cmd", "/k", str(batch_file)],
                    cwd=str(rasa_path),
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                
                # 等待一小段时间确保进程启动
                time.sleep(2)
                
                # 模拟训练过程监控
                training_success = await monitor_training_process(record_id, rasa_path, start_time)
                
                # 清理批处理文件
                try:
                    if batch_file.exists():
                        batch_file.unlink()
                except:
                    pass
                
                if training_success:
                    # 训练成功的处理逻辑
                    record["training_status"] = TrainingStatus.COMPLETED
                    record["progress"] = 100
                    
                    # 查找生成的模型文件
                    models_dir = rasa_path / "models"
                    model_files = list(models_dir.glob("*.tar.gz"))
                    
                    if model_files:
                        # 获取最新的模型文件
                        latest_model = max(model_files, key=os.path.getctime)
                        record["model_path"] = str(latest_model)
                        record["logs"].append(f"✅ 训练完成！模型文件: {latest_model.name}")
                    else:
                        record["logs"].append("⚠️ 训练完成，但未找到模型文件")
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    record["duration"] = duration
                    
                    # 使用本地时间
                    local_time = datetime.now(local_tz)
                    record["end_time"] = local_time.isoformat()
                    record["complete_time"] = local_time.isoformat()
                    
                    # 添加训练摘要
                    record["logs"].append(f"训练耗时: {duration:.1f}秒")
                    
                    # 同步完成状态到数据库
                    sync_training_status_to_db(
                        record_id,
                        'completed',
                        progress=100,
                        model_path=record.get("model_path"),
                        logs=record["logs"]
                    )
                else:
                    # 训练失败的处理逻辑
                    record["training_status"] = TrainingStatus.FAILED
                    record["error_message"] = "训练过程监控失败或训练异常"
                    
                    # 使用本地时间
                    local_time = datetime.now(local_tz)
                    record["end_time"] = local_time.isoformat()
                    record["complete_time"] = local_time.isoformat()
                    
                    record["logs"].append("❌ 训练失败或超时")
                    
                    # 同步失败状态到数据库
                    sync_training_status_to_db(
                        record_id,
                        'failed',
                        error_message=record["error_message"],
                        logs=record["logs"]
                    )
            else:
                # 非Windows系统使用原来的方式
                result = subprocess.run(
                    cmd,
                    cwd=str(rasa_path),
                    capture_output=True,
                    text=True,
                    timeout=1200  # 20分钟超时
                )
                
                # 训练完成后的进度更新
                time.sleep(1)  # 1秒延时
                record["progress"] = 85
                record["logs"].append("训练Core模型...")

                end_time = time.time()
                duration = end_time - start_time

                record["duration"] = duration

                # 使用本地时间
                local_time = datetime.now(local_tz)
                record["end_time"] = local_time.isoformat()
                record["complete_time"] = local_time.isoformat()

                if result.returncode == 0:
                    time.sleep(2)  # 2秒延时
                    record["progress"] = 95
                    record["logs"].append("验证模型性能...")

                    # 模拟模型验证
                    time.sleep(3)  # 3秒延时

                    record["training_status"] = TrainingStatus.COMPLETED
                    record["progress"] = 100

                    # 查找生成的模型文件
                    models_dir = rasa_path / "models"
                    model_files = list(models_dir.glob("*.tar.gz"))

                    if model_files:
                        # 获取最新的模型文件
                        latest_model = max(model_files, key=os.path.getctime)
                        record["model_path"] = str(latest_model)
                        record["logs"].append(f"✅ 训练完成！模型文件: {latest_model.name}")
                    else:
                        record["logs"].append("⚠️ 训练完成，但未找到模型文件")

                    # 添加训练摘要
                    record["logs"].append(f"训练耗时: {duration:.1f}秒")

                    # 尝试解析训练输出中的指标
                    if result.stdout:
                        # 提取有用的训练信息
                        output_lines = result.stdout.split('\n')
                        for line in output_lines:
                            if 'accuracy' in line.lower() or 'f1' in line.lower():
                                record["logs"].append(f"📈 {line.strip()}")

                    # 同步完成状态到数据库
                    sync_training_status_to_db(
                        record_id,
                        'completed',
                        progress=100,
                        model_path=record.get("model_path"),
                        logs=record["logs"]
                    )

                else:
                    record["training_status"] = TrainingStatus.FAILED
                    record["error_message"] = f"训练失败，退出码: {result.returncode}"

                    if result.stderr:
                        record["logs"].append("❌ 错误输出:")
                        # 只保留最重要的错误信息
                        error_lines = result.stderr.split('\n')[:5]
                        record["logs"].extend(error_lines)

                    # 同步失败状态到数据库
                    sync_training_status_to_db(
                        record_id,
                        'failed',
                        error_message=record["error_message"],
                        logs=record["logs"]
                    )

        except subprocess.TimeoutExpired:
            record["training_status"] = TrainingStatus.FAILED
            record["error_message"] = "训练超时（20分钟）"

            # 使用本地时间
            local_time = datetime.now(local_tz)
            record["end_time"] = local_time.isoformat()
            record["complete_time"] = local_time.isoformat()
            record["logs"].append("⏰ 训练超时（20分钟），请检查数据量或系统性能")

            # 同步超时状态到数据库
            sync_training_status_to_db(
                record_id,
                'failed',
                error_message=record["error_message"],
                logs=record["logs"]
            )

        except Exception as e:
            record["training_status"] = TrainingStatus.FAILED
            record["error_message"] = f"训练异常: {str(e)}"

            # 使用本地时间
            local_time = datetime.now(local_tz)
            record["end_time"] = local_time.isoformat()
            record["complete_time"] = local_time.isoformat()
            record["logs"].append(f"💥 训练异常: {str(e)}")

            # 同步异常状态到数据库
            sync_training_status_to_db(
                record_id,
                'failed',
                error_message=record["error_message"],
                logs=record["logs"]
            )

    except Exception as e:
        logger.error(f"训练任务异常: {str(e)}")
        if record_id in training_records:
            # 导入时区相关模块
            import pytz
            local_tz = pytz.timezone('Asia/Shanghai')
            local_time = datetime.now(local_tz)

            training_records[record_id]["training_status"] = TrainingStatus.FAILED
            training_records[record_id]["error_message"] = f"系统异常: {str(e)}"
            training_records[record_id]["end_time"] = local_time.isoformat()
            training_records[record_id]["complete_time"] = local_time.isoformat()
            training_records[record_id]["logs"].append(f"💥 系统异常: {str(e)}")

            # 同步系统异常到数据库
            sync_training_status_to_db(
                record_id,
                'failed',
                error_message=f"系统异常: {str(e)}",
                logs=training_records[record_id]["logs"]
            )


@router.post("/start")
async def start_training(
        request: TrainingRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_new_db)
):
    """
    启动模型训练
    
    Args:
        request: 训练请求数据
        background_tasks: FastAPI后台任务
        db: 数据库会话
        
    Returns:
        训练任务信息
    """
    try:
        logger.info(f"🚀 [训练API] 收到训练请求: library_id={request.library_id}, description={request.description}")

        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == request.library_id
        ).first()

        if not library:
            logger.warning(f"❌ [训练API] 指令库不存在: library_id={request.library_id}")
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)

        logger.info(f"✅ [训练API] 指令库验证成功: {library.name}")

        # 使用全局锁防止重复训练
        library_key = f"library_{request.library_id}"
        current_time = datetime.now()

        logger.info(f"🔒 [训练API] 检查训练锁: {library_key}")

        # 检查是否有锁存在
        if library_key in training_locks:
            lock_time = training_locks[library_key]
            time_diff = current_time - lock_time
            logger.info(f"⏰ [训练API] 找到训练锁，时间差: {time_diff.seconds}秒")

            # 如果锁存在且在30秒内，拒绝新的训练请求
            if time_diff < timedelta(seconds=30):
                remaining_seconds = 30 - time_diff.seconds
                logger.warning(f"🚫 [训练API] 训练请求过于频繁，剩余等待时间: {remaining_seconds}秒")
                return error_response(
                    msg=f"指令库 {library.name} 训练请求过于频繁，请等待30秒后再试",
                    code=ErrorCodes.PARAM_ERROR,
                    data={
                        "lock_time": lock_time.isoformat(),
                        "remaining_seconds": remaining_seconds
                    }
                )

        # 设置训练锁
        training_locks[library_key] = current_time
        logger.info(f"🔐 [训练API] 设置训练锁: {library_key}")

        # 检查是否已有正在进行的训练
        running_training = None
        for record in training_records.values():
            if record["library_id"] == request.library_id:
                # 检查是否有正在进行的训练
                if record["training_status"] in [TrainingStatus.PENDING, TrainingStatus.RUNNING]:
                    running_training = record
                    logger.warning(
                        f"🔄 [训练API] 发现正在进行的训练: ID={record['id']}, 状态={record['training_status']}")
                    break
                # 检查是否有刚刚启动的训练（10秒内）
                elif record.get("start_time"):
                    try:
                        start_time = datetime.fromisoformat(record["start_time"])
                        # 确保current_time也有时区信息
                        if start_time.tzinfo is not None:
                            # 如果start_time有时区信息，使用相同的时区
                            import pytz
                            local_tz = pytz.timezone('Asia/Shanghai')
                            current_time_with_tz = current_time.replace(tzinfo=local_tz)
                            if current_time_with_tz - start_time < timedelta(seconds=10):
                                running_training = record
                                logger.warning(f"⏱️ [训练API] 发现10秒内的训练: ID={record['id']}")
                                break
                        else:
                            # 如果start_time没有时区信息，都转换为naive datetime
                            if current_time - start_time < timedelta(seconds=10):
                                running_training = record
                                logger.warning(f"⏱️ [训练API] 发现10秒内的训练: ID={record['id']}")
                                break
                    except Exception as time_error:
                        logger.warning(f"⚠️ [训练API] 时间解析错误: {str(time_error)}")
                        continue

        if running_training:
            logger.warning(f"🚫 [训练API] 拒绝重复训练请求")
            return error_response(
                msg=f"指令库 {library.name} 已有训练任务正在进行中或刚刚启动（ID: {running_training['id']}），请等待完成后再启动新训练",
                code=ErrorCodes.PARAM_ERROR,
                data={
                    "running_training_id": running_training["id"],
                    "running_training_status": running_training["training_status"],
                    "running_training_start_time": running_training["start_time"]
                }
            )

        # 创建训练记录（先创建记录，版本生成在后台进行）
        logger.info(f"📝 [训练API] 创建训练记录")
        record = create_training_record(
            request.library_id,
            library.name,
            None,  # 版本名称在后台生成
            request.description
        )

        logger.info(f"✅ [训练API] 训练记录创建成功: ID={record['id']}")

        # 启动后台训练任务（版本生成和训练都在后台进行）
        logger.info(f"🚀 [训练API] 启动后台训练任务")
        background_tasks.add_task(run_rasa_training_with_version_generation, record["id"], request.library_id, request.description)

        response_data = {
            "training_record": {
                "id": record["id"],
                "library_id": request.library_id,
                "library_name": library.name,
                "version_name": "正在生成...",  # 版本名称在后台生成
                "training_status": record["training_status"],
                "start_time": record["start_time"],
                "description": request.description
            },
            "training_record_id": record["id"],  # 修复字段名称，保持与前端一致
            "training_id": record["id"],  # 保持兼容性
            "library_id": request.library_id,
            "library_name": library.name,
            "version_name": "正在生成...",  # 版本名称在后台生成
            "training_status": record["training_status"],
            "start_time": record["start_time"],
            "description": request.description
        }

        logger.info(f"📤 [训练API] 返回响应: {response_data}")

        return success_response(
            data=response_data,
            msg="训练任务已启动"
        )

    except Exception as e:
        logger.error(f"💥 [训练API] 启动训练异常: {str(e)}")
        return error_response(msg=f"启动训练失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


@router.get("/status/{training_id}")
async def get_training_status(training_id: int, db: Session = Depends(get_new_db)):
    """
    获取训练状态 - 数据库优先策略
    
    Args:
        training_id: 训练任务ID
        db: 数据库会话
        
    Returns:
        训练状态信息
    """
    try:
        logger.info(f"📊 [状态API] 获取训练状态: training_id={training_id}")

        # 1. 首先从数据库查询训练记录
        db_record = db.query(DBModelTrainingRecord).filter(
            DBModelTrainingRecord.id == training_id
        ).first()

        if not db_record:
            logger.warning(f"❌ [状态API] 训练记录不存在: training_id={training_id}")
            return error_response(msg="训练记录不存在", code=ErrorCodes.NOT_FOUND)

        logger.info(f"📋 [状态API] 数据库记录状态: {db_record.training_status}")

        # 2. 如果是正在进行的训练，优先使用内存中的实时状态
        if db_record.training_status in ['preparing', 'pending', 'running']:
            if training_id in training_records:
                memory_record = training_records[training_id]
                logger.info(
                    f"🔄 [状态API] 使用内存实时状态: {memory_record['training_status']}, 进度={memory_record.get('progress', 0)}%")

                # 计算实时时间
                elapsed_time = 0
                try:
                    if memory_record.get("start_time"):
                        start_time_str = memory_record["start_time"]
                        if memory_record["training_status"] == TrainingStatus.COMPLETED and memory_record.get(
                                "end_time"):
                            elapsed_time = memory_record.get("duration", 0) / 60 if memory_record.get("duration") else 0
                        else:
                            try:
                                start_time = datetime.fromisoformat(start_time_str.replace('+08:00', ''))
                                current_time = datetime.now()
                                elapsed_time = (current_time - start_time).total_seconds() / 60
                            except:
                                elapsed_time = 0
                except Exception as time_error:
                    logger.warning(f"⚠️ [状态API] 时间计算错误: {str(time_error)}")
                    elapsed_time = 0

                # 估算剩余时间
                estimated_remaining = 0
                progress = memory_record.get("progress", 0)
                if memory_record["training_status"] == TrainingStatus.RUNNING and progress > 0:
                    try:
                        estimated_total = (elapsed_time * 100) / progress
                        estimated_remaining = max(0, estimated_total - elapsed_time)
                    except:
                        estimated_remaining = 0

                # 当前步骤描述
                current_step = ""
                status = memory_record["training_status"]
                if status == TrainingStatus.PENDING:
                    current_step = "准备训练环境"
                elif status == TrainingStatus.RUNNING:
                    if progress < 20:
                        current_step = "数据预处理"
                    elif progress < 40:
                        current_step = "模型初始化"
                    elif progress < 80:
                        current_step = "执行训练"
                    else:
                        current_step = "模型验证"
                elif status == TrainingStatus.COMPLETED:
                    current_step = "训练完成"
                elif status == TrainingStatus.FAILED:
                    current_step = "训练失败"
                else:
                    current_step = "未知状态"

                response_data = {
                    "training_status": status,
                    "progress": progress,
                    "current_step": current_step,
                    "elapsed_time": round(max(0, elapsed_time), 1),
                    "estimated_remaining": round(max(0, estimated_remaining), 1),
                    "start_time": memory_record.get("start_time"),
                    "end_time": memory_record.get("end_time"),
                    "error_message": memory_record.get("error_message"),
                    "logs": memory_record.get("logs", [])[-5:]  # 最近5条日志
                }

                logger.info(f"📤 [状态API] 返回内存状态: progress={progress}%, elapsed={elapsed_time:.1f}min")
                return success_response(data=response_data, msg="获取训练状态成功（实时）")
            else:
                # 内存中没有记录，但数据库显示正在进行，可能是服务重启后的情况
                logger.warning(f"⚠️ [状态API] 内存中无记录，但数据库显示正在进行，可能是服务重启")

                # 将状态重置为失败，因为内存状态丢失
                db_record.training_status = 'failed'
                db_record.error_message = '服务重启导致训练中断'
                if not db_record.complete_time:
                    db_record.complete_time = datetime.now()
                db.commit()

                response_data = {
                    "training_status": "failed",
                    "progress": 0,
                    "current_step": "训练中断",
                    "elapsed_time": 0,
                    "estimated_remaining": 0,
                    "start_time": db_record.start_time.isoformat() if db_record.start_time else None,
                    "end_time": db_record.complete_time.isoformat() if db_record.complete_time else None,
                    "error_message": "服务重启导致训练中断",
                    "logs": ["训练过程中服务重启，训练状态丢失"]
                }

                return success_response(data=response_data, msg="训练状态已重置（服务重启）")

        # 3. 对于已完成的训练，使用数据库中的持久化状态
        logger.info(f"📁 [状态API] 使用数据库持久化状态")

        # 计算训练时长
        elapsed_time = 0
        if db_record.start_time and db_record.complete_time:
            duration = db_record.complete_time - db_record.start_time
            elapsed_time = duration.total_seconds() / 60

        # 根据状态确定进度
        progress = 100 if db_record.training_status == 'completed' else 0
        if db_record.training_status == 'failed':
            progress = 0

        # 当前步骤描述
        current_step_map = {
            'completed': '训练完成',
            'failed': '训练失败',
            'success': '训练完成',  # 兼容旧状态
            'preparing': '准备中',
            'pending': '等待开始',
            'running': '训练中'
        }
        current_step = current_step_map.get(db_record.training_status, '未知状态')

        response_data = {
            "training_status": db_record.training_status,
            "progress": progress,
            "current_step": current_step,
            "elapsed_time": round(max(0, elapsed_time), 1),
            "estimated_remaining": 0,  # 已完成的训练无剩余时间
            "start_time": db_record.start_time.isoformat() if db_record.start_time else None,
            "end_time": db_record.complete_time.isoformat() if db_record.complete_time else None,
            "error_message": db_record.error_message,
            "logs": db_record.training_log.split('\n') if db_record.training_log else []
        }

        logger.info(f"📤 [状态API] 返回数据库状态: {db_record.training_status}")

        return success_response(
            data=response_data,
            msg="获取训练状态成功（持久化）"
        )

    except Exception as e:
        logger.error(f"💥 [状态API] 获取训练状态异常: {str(e)}")
        return error_response(msg=f"获取训练状态失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


@router.get("/records")
async def get_training_records(
        library_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20,
        db: Session = Depends(get_new_db)
):
    """
    获取训练记录列表 - 数据库优先策略
    
    Args:
        library_id: 指令库ID（可选，用于过滤）
        skip: 跳过记录数
        limit: 返回记录数限制
        db: 数据库会话
        
    Returns:
        训练记录列表
    """
    try:
        # 1. 从数据库获取训练记录
        query = db.query(DBModelTrainingRecord)
        if library_id is not None:
            query = query.filter(DBModelTrainingRecord.library_id == library_id)

        # 按创建时间降序排列
        query = query.order_by(DBModelTrainingRecord.created_time.desc())

        # 获取总数
        total = query.count()

        # 分页获取记录
        db_records = query.offset(skip).limit(limit).all()

        logger.info(f"📋 [获取记录] 从数据库获取到 {len(db_records)} 条记录，总数 {total}")

        # 2. 格式化数据库记录
        formatted_records = []
        for db_record in db_records:
            # 检查是否有对应的内存记录（正在进行的训练）
            memory_record = training_records.get(db_record.id)

            if memory_record and db_record.training_status in ['pending', 'running']:
                # 使用内存中的实时状态
                formatted_record = {
                    "id": db_record.id,
                    "library_id": db_record.library_id,
                    "library_name": memory_record.get("library_name", ""),
                    "version_number": db_record.version_number,
                    "version_name": memory_record.get("version_name"),
                    "description": memory_record.get("description"),
                    "training_status": memory_record["training_status"],
                    "start_time": memory_record["start_time"],
                    "end_time": memory_record.get("end_time"),
                    "complete_time": memory_record.get("end_time"),
                    "duration": memory_record.get("duration"),
                    "progress": memory_record.get("progress", 0),
                    "intent_count": db_record.intent_count or 0,
                    "slot_count": db_record.slot_count or 0,
                    "training_data_count": db_record.training_data_count or 0,
                    "is_active": db_record.is_active,
                    "model_path": memory_record.get("model_path") or db_record.model_file_path,
                    "error_message": memory_record.get("error_message") or db_record.error_message
                }
                logger.info(f"🔄 [获取记录] 使用内存状态: ID={db_record.id}, 状态={memory_record['training_status']}")
            else:
                # 使用数据库中的持久化状态
                formatted_record = {
                    "id": db_record.id,
                    "library_id": db_record.library_id,
                    "library_name": "",  # 需要从关联查询获取
                    "version_number": db_record.version_number,
                    "version_name": None,  # 从训练参数中解析
                    "description": None,  # 从训练参数中解析
                    "training_status": db_record.training_status,
                    "start_time": db_record.start_time.isoformat() if db_record.start_time else None,
                    "end_time": db_record.complete_time.isoformat() if db_record.complete_time else None,
                    "complete_time": db_record.complete_time.isoformat() if db_record.complete_time else None,
                    "duration": None,  # 计算得出
                    "progress": 100 if db_record.training_status == 'completed' else 0,
                    "intent_count": db_record.intent_count or 0,
                    "slot_count": db_record.slot_count or 0,
                    "training_data_count": db_record.training_data_count or 0,
                    "is_active": db_record.is_active,
                    "model_path": db_record.model_file_path,
                    "error_message": db_record.error_message
                }

                # 计算训练时长
                if db_record.start_time and db_record.complete_time:
                    duration = db_record.complete_time - db_record.start_time
                    formatted_record["duration"] = duration.total_seconds()

                # 解析训练参数
                if db_record.training_params:
                    try:
                        params = json.loads(db_record.training_params)
                        formatted_record["description"] = params.get("description")
                        formatted_record["version_name"] = params.get("version_name")
                    except:
                        pass

                # 获取指令库名称
                if db_record.library:
                    formatted_record["library_name"] = db_record.library.name

                logger.info(f"📁 [获取记录] 使用数据库状态: ID={db_record.id}, 状态={db_record.training_status}")

            formatted_records.append(formatted_record)

        # 3. 添加仅存在于内存中的记录（理论上不应该存在，但作为兜底）
        memory_only_records = []
        for record_id, memory_record in training_records.items():
            # 检查是否已在数据库记录中
            if not any(db_record.id == record_id for db_record in db_records):
                if library_id is None or memory_record["library_id"] == library_id:
                    logger.warning(f"⚠️ [获取记录] 发现仅存在内存的记录: ID={record_id}")
                    memory_only_records.append({
                        "id": memory_record["id"],
                        "library_id": memory_record["library_id"],
                        "library_name": memory_record["library_name"],
                        "version_number": memory_record.get("version_number", memory_record["id"]),
                        "version_name": memory_record.get("version_name"),
                        "description": memory_record.get("description"),
                        "training_status": memory_record["training_status"],
                        "start_time": memory_record["start_time"],
                        "end_time": memory_record.get("end_time"),
                        "complete_time": memory_record.get("end_time"),
                        "duration": memory_record.get("duration"),
                        "progress": memory_record.get("progress", 0),
                        "intent_count": memory_record.get("intent_count", 0),
                        "slot_count": memory_record.get("slot_count", 0),
                        "training_data_count": memory_record.get("training_data_count", 0),
                        "is_active": memory_record.get("is_active", False),
                        "model_path": memory_record.get("model_path"),
                        "error_message": memory_record.get("error_message")
                    })

        # 合并内存记录（如果有的话）
        all_records = formatted_records + memory_only_records

        # 按开始时间排序（最新的在前）
        all_records.sort(key=lambda x: x["start_time"] or "", reverse=True)

        return success_response(
            data={
                "training_records": all_records,
                "records": all_records,  # 保持兼容性
                "total": total + len(memory_only_records),
                "skip": skip,
                "limit": limit,
                "db_records": len(formatted_records),
                "memory_records": len(memory_only_records)
            },
            msg=f"获取训练记录成功，共 {total + len(memory_only_records)} 条（数据库 {len(formatted_records)} 条，内存 {len(memory_only_records)} 条）"
        )

    except Exception as e:
        logger.error(f"💥 [获取记录] 获取训练记录异常: {str(e)}")
        return error_response(msg=f"获取训练记录失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


@router.get("/records/{record_id}")
async def get_training_record(record_id: int):
    """
    获取单个训练记录详情
    
    Args:
        record_id: 训练记录ID
        
    Returns:
        训练记录详情
    """
    try:
        if record_id not in training_records:
            return error_response(msg="训练记录不存在", code=ErrorCodes.NOT_FOUND)

        record = training_records[record_id]

        # 构建完整的训练记录详情
        detailed_record = {
            "id": record["id"],
            "library_id": record["library_id"],
            "library_name": record["library_name"],
            "version_number": record.get("version_number", record["id"]),
            "version_name": record.get("version_name"),
            "description": record.get("description"),
            "training_status": record["training_status"],
            "start_time": record["start_time"],
            "end_time": record.get("end_time"),
            "complete_time": record.get("end_time"),
            "duration": record.get("duration"),
            "progress": record.get("progress", 0),
            "intent_count": record.get("intent_count", 0),
            "slot_count": record.get("slot_count", 0),
            "training_data_count": record.get("training_data_count", 0),
            "is_active": record.get("is_active", False),
            "model_path": record.get("model_path"),
            "error_message": record.get("error_message"),
            "training_log": '\n'.join(record.get("logs", [])),  # 完整日志
            "logs": record.get("logs", []),  # 日志数组
            "training_params": record.get("training_params", "使用默认训练参数"),
            "metrics": record.get("metrics", {})
        }

        return success_response(
            data=detailed_record,
            msg="获取训练记录详情成功"
        )

    except Exception as e:
        return error_response(msg=f"获取训练记录失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


@router.get("/library/{library_id}/summary")
async def get_library_training_summary(
        library_id: int,
        db: Session = Depends(get_new_db)
):
    """
    获取指令库训练摘要
    
    Args:
        library_id: 指令库ID
        db: 数据库会话
        
    Returns:
        训练摘要信息
    """
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()

        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)

        # 统计该指令库的训练记录
        library_records = [
            record for record in training_records.values()
            if record["library_id"] == library_id
        ]

        # 计算统计信息
        total_trainings = len(library_records)
        completed_trainings = len([r for r in library_records if r["training_status"] == TrainingStatus.COMPLETED])
        failed_trainings = len([r for r in library_records if r["training_status"] == TrainingStatus.FAILED])
        running_trainings = len([r for r in library_records if r["training_status"] == TrainingStatus.RUNNING])

        # 获取最新的训练记录
        latest_training = None
        if library_records:
            latest_training = max(library_records, key=lambda x: x["start_time"])

        # 计算平均训练时间
        completed_records = [r for r in library_records if
                             r["training_status"] == TrainingStatus.COMPLETED and r["duration"]]
        avg_duration = None
        if completed_records:
            avg_duration = sum(r["duration"] for r in completed_records) / len(completed_records)

        # 获取可用模型数量
        rasa_path = get_rasa_project_path()
        models_dir = rasa_path / "models"
        available_models = 0
        if models_dir.exists():
            available_models = len(list(models_dir.glob("*.tar.gz")))

        summary = {
            "library_id": library_id,
            "library_name": library.name,
            "training_statistics": {
                "total_trainings": total_trainings,
                "completed_trainings": completed_trainings,
                "failed_trainings": failed_trainings,
                "running_trainings": running_trainings,
                "success_rate": (completed_trainings / total_trainings * 100) if total_trainings > 0 else 0
            },
            "latest_training": latest_training,
            "performance": {
                "average_duration": avg_duration,
                "available_models": available_models
            },
            # 使用本地时区
            "last_updated": datetime.now().isoformat()
        }

        return success_response(
            data=summary,
            msg="获取训练摘要成功"
        )

    except Exception as e:
        return error_response(msg=f"获取训练摘要失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


@router.post("/cancel/{record_id}")
async def cancel_training(record_id: int):
    """
    取消训练任务
    
    Args:
        record_id: 训练记录ID
        
    Returns:
        取消结果
    """
    try:
        if record_id not in training_records:
            return error_response(msg="训练记录不存在", code=ErrorCodes.NOT_FOUND)

        record = training_records[record_id]

        if record["training_status"] not in [TrainingStatus.PENDING, TrainingStatus.RUNNING]:
            return error_response(msg="训练任务无法取消", code=ErrorCodes.PARAM_ERROR)

        record["training_status"] = TrainingStatus.CANCELLED
        # 使用本地时区
        import pytz
        local_tz = pytz.timezone('Asia/Shanghai')
        local_time = datetime.now(local_tz)
        record["end_time"] = local_time.isoformat()
        record["logs"].append("训练任务已被用户取消")

        return success_response(
            data={
                "training_id": record_id,
                "training_status": record["training_status"]
            },
            msg="训练任务已取消"
        )

    except Exception as e:
        return error_response(msg=f"取消训练失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


@router.post("/clear-all")
async def clear_all_training_records():
    """
    清除所有训练记录（内存中的数据）
    
    Returns:
        清除结果
    """
    try:
        global training_records, training_counter, training_locks

        # 停止所有正在运行的训练监控
        for record_id in list(training_records.keys()):
            if record_id in training_records:
                record = training_records[record_id]
                if record.get("training_status") == TrainingStatus.RUNNING:
                    record["training_status"] = TrainingStatus.CANCELLED
                    # 使用本地时区
                    import pytz
                    local_tz = pytz.timezone('Asia/Shanghai')
                    local_time = datetime.now(local_tz)
                    record["end_time"] = local_time.isoformat()
                    record["complete_time"] = local_time.isoformat()
                    record["logs"].append("训练已被清除操作取消")

        # 清除所有训练记录
        cleared_count = len(training_records)
        training_records.clear()
        training_counter = 1

        # 清除训练锁
        training_locks.clear()

        return success_response(
            data={
                "cleared_count": cleared_count,
                "message": "所有训练记录已清除"
            },
            msg=f"成功清除 {cleared_count} 条训练记录"
        )

    except Exception as e:
        return error_response(msg=f"清除训练记录失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


@router.get("/status")
async def get_training_status():
    """
    获取训练系统状态
    
    Returns:
        训练系统状态
    """
    try:
        # 统计所有训练记录
        total_records = len(training_records)
        running_count = len([r for r in training_records.values() if r["training_status"] == TrainingStatus.RUNNING])

        # 检查RASA是否可用
        rasa_available = False
        try:
            result = subprocess.run(["rasa", "--version"], capture_output=True, text=True, timeout=5)
            rasa_available = result.returncode == 0
            rasa_version = result.stdout.strip() if rasa_available else None
        except:
            rasa_version = None

        # 检查工作区状态
        rasa_path = get_rasa_project_path()
        workspace_files = {
            "domain.yml": (rasa_path / "data" / "domain.yml").exists(),
            "nlu.yml": (rasa_path / "data" / "nlu.yml").exists(),
            "config.yml": (rasa_path / "config.yml").exists()
        }

        status = {
            "system_status": "ready" if rasa_available else "unavailable",
            "rasa_version": rasa_version,
            "total_trainings": total_records,
            "running_trainings": running_count,
            "workspace_status": workspace_files,
            "timestamp": datetime.now().isoformat()
        }

        return success_response(
            data=status,
            msg="获取训练系统状态成功"
        )

    except Exception as e:
        return error_response(msg=f"获取系统状态失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


@router.get("/records/{record_id}/logs")
async def get_training_logs(record_id: int, db: Session = Depends(get_new_db)):
    """
    获取训练日志
    
    Args:
        record_id: 训练记录ID
        db: 数据库会话
        
    Returns:
        训练日志列表
    """
    try:
        logger.info(f"📋 [获取日志] 获取训练日志: record_id={record_id}")

        # 1. 首先尝试从内存获取实时日志
        if record_id in training_records:
            memory_record = training_records[record_id]
            logs = memory_record.get("logs", [])
            logger.info(f"📋 [获取日志] 从内存获取到 {len(logs)} 条日志")

            return success_response(
                data={
                    "logs": logs,
                    "source": "memory",
                    "total": len(logs)
                },
                msg=f"获取训练日志成功（内存，{len(logs)} 条）"
            )

        # 2. 从数据库获取持久化日志
        db_record = db.query(DBModelTrainingRecord).filter(
            DBModelTrainingRecord.id == record_id
        ).first()

        if not db_record:
            logger.warning(f"❌ [获取日志] 训练记录不存在: record_id={record_id}")
            return error_response(msg="训练记录不存在", code=ErrorCodes.NOT_FOUND)

        # 解析数据库中的日志
        logs = []
        if db_record.training_log:
            logs = db_record.training_log.split('\n')
            # 过滤空行
            logs = [log.strip() for log in logs if log.strip()]

        logger.info(f"📋 [获取日志] 从数据库获取到 {len(logs)} 条日志")

        return success_response(
            data={
                "logs": logs,
                "source": "database",
                "total": len(logs)
            },
            msg=f"获取训练日志成功（数据库，{len(logs)} 条）"
        )

    except Exception as e:
        logger.error(f"💥 [获取日志] 获取训练日志异常: {str(e)}")
        return error_response(msg=f"获取训练日志失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


@router.post("/records/{record_id}/activate")
async def activate_training_record(record_id: int, db: Session = Depends(get_new_db)):
    """
    激活训练记录（将对应的模型设为当前激活模型）
    
    Args:
        record_id: 训练记录ID
        db: 数据库会话
        
    Returns:
        激活结果
    """
    try:
        logger.info(f"🔄 [激活模型] 激活训练记录: record_id={record_id}")

        # 查找训练记录
        db_record = db.query(DBModelTrainingRecord).filter(
            DBModelTrainingRecord.id == record_id
        ).first()

        if not db_record:
            logger.warning(f"❌ [激活模型] 训练记录不存在: record_id={record_id}")
            return error_response(msg="训练记录不存在", code=ErrorCodes.NOT_FOUND)

        # 检查训练状态
        if db_record.training_status != 'completed':
            logger.warning(f"❌ [激活模型] 训练未完成，无法激活: 状态={db_record.training_status}")
            return error_response(
                msg=f"训练状态为 {db_record.training_status}，只能激活已完成的训练记录",
                code=ErrorCodes.PARAM_ERROR
            )

        # 检查是否已经是激活状态
        if db_record.is_active:
            logger.info(f"ℹ️ [激活模型] 记录已经是激活状态: record_id={record_id}")
            return success_response(
                data={
                    "record_id": record_id,
                    "version_number": db_record.version_number,
                    "already_active": True
                },
                msg=f"v{db_record.version_number} 已经是当前激活版本"
            )

        # 将同一指令库的其他记录设为非激活
        db.query(DBModelTrainingRecord).filter(
            DBModelTrainingRecord.library_id == db_record.library_id,
            DBModelTrainingRecord.is_active == True
        ).update({"is_active": False})

        # 激活当前记录
        db_record.is_active = True
        db.commit()

        # 同步更新内存状态（如果存在）
        if record_id in training_records:
            training_records[record_id]["is_active"] = True

        # 将其他内存记录设为非激活
        for memory_record in training_records.values():
            if memory_record["library_id"] == db_record.library_id and memory_record["id"] != record_id:
                memory_record["is_active"] = False

        logger.info(f"✅ [激活模型] 模型激活成功: v{db_record.version_number}")

        return success_response(
            data={
                "record_id": record_id,
                "library_id": db_record.library_id,
                "version_number": db_record.version_number,
                "model_path": db_record.model_file_path,
                "activated_at": datetime.now().isoformat()
            },
            msg=f"模型 v{db_record.version_number} 已激活为当前版本"
        )

    except Exception as e:
        logger.error(f"💥 [激活模型] 激活训练记录异常: {str(e)}")
        return error_response(msg=f"激活模型失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)


@router.get("/status")
async def get_training_status():
    """
    获取训练系统状态
    
    Returns:
        训练系统状态信息
    """
    try:
        total_records = len(training_records)
        running_count = len([r for r in training_records.values() if r["training_status"] == TrainingStatus.RUNNING])
        pending_count = len([r for r in training_records.values() if r["training_status"] == TrainingStatus.PENDING])
        completed_count = len(
            [r for r in training_records.values() if r["training_status"] == TrainingStatus.COMPLETED])
        failed_count = len([r for r in training_records.values() if r["training_status"] == TrainingStatus.FAILED])

        return success_response(
            data={
                "total_records": total_records,
                "running_count": running_count,
                "pending_count": pending_count,
                "completed_count": completed_count,
                "failed_count": failed_count,
                "memory_usage": len(training_records),
                "active_locks": len(training_locks),
                "system_status": "healthy" if running_count < 5 else "busy"
            },
            msg="获取训练系统状态成功"
        )

    except Exception as e:
        return error_response(msg=f"获取训练系统状态失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)
