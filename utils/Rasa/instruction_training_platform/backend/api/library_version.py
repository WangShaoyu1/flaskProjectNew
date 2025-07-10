"""
指令库版本管理API
管理Excel解析后的YML文件与指令库版本的关联
"""

from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import json
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.database_models import get_new_db, InstructionLibraryMaster as DBInstructionLibraryMaster
from services.library_version_manager import LibraryVersionManager
from services.dual_screen_processor import DualScreenProcessor
from response_utils import StandardResponse, success_response, error_response, ErrorCodes

router = APIRouter(prefix="/api/v2/library-version", tags=["指令库版本管理"])

# 初始化版本管理器
version_manager = LibraryVersionManager()

@router.post("/create-from-excel")
async def create_version_from_excel(
    library_id: int = Form(..., description="指令库ID"),
    instruction_file: UploadFile = File(..., description="指令Excel文件"),
    slot_file: UploadFile = File(..., description="词槽Excel文件"),
    version_name: Optional[str] = Form(None, description="版本名称"),
    description: str = Form("", description="版本描述"),
    db: Session = Depends(get_new_db)
):
    """
    从Excel文件创建指令库版本
    
    Args:
        library_id: 指令库ID
        instruction_file: 指令Excel文件
        slot_file: 词槽Excel文件
        version_name: 版本名称（可选）
        description: 版本描述
        db: 数据库会话
        
    Returns:
        创建结果
    """
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 验证文件格式
        if not instruction_file.filename.endswith(('.xlsx', '.xls')):
            return error_response(msg="指令文件必须是Excel格式", code=ErrorCodes.PARAM_ERROR)
        
        if not slot_file.filename.endswith(('.xlsx', '.xls')):
            return error_response(msg="词槽文件必须是Excel格式", code=ErrorCodes.PARAM_ERROR)
        
        # 处理Excel文件
        processor = DualScreenProcessor()
        
        # 读取文件内容
        instruction_content = await instruction_file.read()
        slot_content = await slot_file.read()
        
        # 保存临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_instruction:
            temp_instruction.write(instruction_content)
            instruction_path = temp_instruction.name
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_slot:
            temp_slot.write(slot_content)
            slot_path = temp_slot.name
        
        try:
            # 处理数据
            processor.process_slot_data(slot_path)
            processor.process_instruction_data(instruction_path)
            
            # 生成YML文件内容
            file_contents = {
                'nlu.yml': processor.generate_nlu_yml(),
                'domain.yml': processor.generate_domain_yml(),
                'rules.yml': processor.generate_rules_yml(),
                'stories.yml': processor.generate_stories_yml()
            }
            
            # 保存版本
            version_name_result = version_manager.save_excel_generated_files(
                library_id=library_id,
                library_name=library.name,
                file_contents=file_contents,
                version_name=version_name,
                description=description or f"从Excel导入 - {instruction_file.filename}, {slot_file.filename}"
            )
            
            # 生成统计报告
            report = processor.generate_conversion_report()
            
            return success_response(
                data={
                    "library_id": library_id,
                    "library_name": library.name,
                    "version_name": version_name_result,
                    "description": description,
                    "file_count": len(file_contents),
                    "conversion_report": report,
                    "file_paths": {
                        f"rasa/library_versions/library_{library_id}/{version_name_result}/{filename}": filename
                        for filename in file_contents.keys()
                    }
                },
                msg=f"Excel文件已成功转换并保存为版本 {version_name_result}"
            )
            
        finally:
            # 清理临时文件
            os.unlink(instruction_path)
            os.unlink(slot_path)
            
    except Exception as e:
        return error_response(msg=f"创建版本失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)

@router.get("/list/{library_id}")
async def get_library_versions(
    library_id: int,
    db: Session = Depends(get_new_db)
):
    """
    获取指令库的所有版本
    
    Args:
        library_id: 指令库ID
        db: 数据库会话
        
    Returns:
        版本列表
    """
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 获取版本列表
        versions = version_manager.get_library_versions(library_id)
        
        return success_response(
            data={
                "library_id": library_id,
                "library_name": library.name,
                "versions": versions,
                "total_count": len(versions)
            },
            msg=f"获取指令库 {library.name} 的版本列表成功"
        )
        
    except Exception as e:
        return error_response(msg=f"获取版本列表失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)

@router.get("/files/{library_id}/{version_name}")
async def get_version_files(
    library_id: int,
    version_name: str,
    db: Session = Depends(get_new_db)
):
    """
    获取指定版本的文件内容
    
    Args:
        library_id: 指令库ID
        version_name: 版本名称
        db: 数据库会话
        
    Returns:
        文件内容
    """
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 获取文件内容
        files_content = version_manager.get_version_files(library_id, version_name)
        
        if not files_content:
            return error_response(msg="版本不存在或文件为空", code=ErrorCodes.NOT_FOUND)
        
        return success_response(
            data={
                "library_id": library_id,
                "library_name": library.name,
                "version_name": version_name,
                "files": files_content,
                "file_count": len(files_content)
            },
            msg=f"获取版本 {version_name} 的文件内容成功"
        )
        
    except Exception as e:
        return error_response(msg=f"获取版本文件失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)

@router.post("/activate/{library_id}/{version_name}")
async def activate_version(
    library_id: int,
    version_name: str,
    db: Session = Depends(get_new_db)
):
    """
    激活指定版本到RASA工作区
    
    Args:
        library_id: 指令库ID
        version_name: 版本名称
        db: 数据库会话
        
    Returns:
        激活结果
    """
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 激活版本
        success = version_manager.activate_version(library_id, version_name)
        
        if success:
            return success_response(
                data={
                    "library_id": library_id,
                    "library_name": library.name,
                    "version_name": version_name,
                    "workspace_path": "rasa/data/"
                },
                msg=f"版本 {version_name} 已成功激活到RASA工作区"
            )
        else:
            return error_response(msg="激活版本失败", code=ErrorCodes.SYSTEM_ERROR)
            
    except Exception as e:
        return error_response(msg=f"激活版本失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)

@router.delete("/delete/{library_id}/{version_name}")
async def delete_version(
    library_id: int,
    version_name: str,
    db: Session = Depends(get_new_db)
):
    """
    删除指定版本
    
    Args:
        library_id: 指令库ID
        version_name: 版本名称
        db: 数据库会话
        
    Returns:
        删除结果
    """
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 删除版本
        success = version_manager.delete_version(library_id, version_name)
        
        if success:
            return success_response(
                data={
                    "library_id": library_id,
                    "library_name": library.name,
                    "version_name": version_name
                },
                msg=f"版本 {version_name} 已成功删除"
            )
        else:
            return error_response(msg="版本不存在或删除失败", code=ErrorCodes.NOT_FOUND)
            
    except Exception as e:
        return error_response(msg=f"删除版本失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)

@router.get("/index")
async def get_library_index():
    """
    获取所有指令库的版本索引
    
    Returns:
        版本索引
    """
    try:
        index = version_manager.get_library_index()
        
        return success_response(
            data={
                "index": index,
                "library_count": len(index)
            },
            msg="获取指令库版本索引成功"
        )
        
    except Exception as e:
        return error_response(msg=f"获取版本索引失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR)

@router.post("/create-manual/{library_id}")
async def create_manual_version(
    library_id: int,
    version_name: Optional[str] = Form(None, description="版本名称"),
    description: str = Form("", description="版本描述"),
    db: Session = Depends(get_new_db)
):
    """
    手动创建版本（基于当前工作区）
    
    Args:
        library_id: 指令库ID
        version_name: 版本名称（可选）
        description: 版本描述
        db: 数据库会话
        
    Returns:
        创建结果
    """
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            return error_response(msg="指令库不存在", code=ErrorCodes.NOT_FOUND)
        
        # 创建版本
        version_name_result = version_manager.create_library_version(
            library_id=library_id,
            library_name=library.name,
            version_name=version_name,
            description=description or "手动创建版本"
        )
        
        return success_response(
            data={
                "library_id": library_id,
                "library_name": library.name,
                "version_name": version_name_result,
                "description": description
            },
            msg=f"手动版本 {version_name_result} 创建成功"
        )
        
    except Exception as e:
        return error_response(msg=f"创建版本失败: {str(e)}", code=ErrorCodes.SYSTEM_ERROR) 