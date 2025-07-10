"""
初始化系统词槽
为所有指令库创建Rasa系统支持的基础词槽
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy.orm import Session
from models.database_models import (
    get_new_db, create_new_tables,
    SlotDefinition as DBSlotDefinition,
    InstructionLibraryMaster as DBInstructionLibraryMaster,
    new_engine
)

# 系统词槽定义
SYSTEM_SLOTS = [
    {
        "slot_name": "时长",
        "slot_name_en": "duration",
        "slot_type": "text",
        "description": "时间持续长度，如：15分钟、2小时、3天等",
        "is_system": True,
        "is_required": False,
        "is_active": True
    },
    {
        "slot_name": "数字",
        "slot_name_en": "number",
        "slot_type": "float",
        "description": "数值类型，如：1、2.5、100等",
        "is_system": True,
        "is_required": False,
        "is_active": True
    },
    {
        "slot_name": "数量",
        "slot_name_en": "quantity",
        "slot_type": "text",
        "description": "数量表达，如：一个、两台、三件等",
        "is_system": True,
        "is_required": False,
        "is_active": True
    },
    {
        "slot_name": "时间",
        "slot_name_en": "time",
        "slot_type": "text",
        "description": "时间点，如：上午9点、下午3点、晚上8点等",
        "is_system": True,
        "is_required": False,
        "is_active": True
    },
    {
        "slot_name": "音量",
        "slot_name_en": "volume",
        "slot_type": "text",
        "description": "音量大小，如：大声、小声、50%等",
        "is_system": True,
        "is_required": False,
        "is_active": True
    }
]


def init_system_slots_for_library(db: Session, library_id: int):
    """为指定指令库初始化系统词槽"""
    created_count = 0
    updated_count = 0
    
    for slot_config in SYSTEM_SLOTS:
        # 检查系统词槽是否已存在
        existing_slot = db.query(DBSlotDefinition).filter(
            DBSlotDefinition.library_id == library_id,
            DBSlotDefinition.slot_name_en == slot_config["slot_name_en"],
            DBSlotDefinition.is_system == True
        ).first()
        
        if existing_slot:
            # 更新现有系统词槽
            for key, value in slot_config.items():
                if key != "slot_name_en":  # 不更新英文名
                    setattr(existing_slot, key, value)
            updated_count += 1
            print(f"  更新系统词槽: {slot_config['slot_name']} ({slot_config['slot_name_en']})")
        else:
            # 创建新的系统词槽
            slot_data = {
                "library_id": library_id,
                **slot_config
            }
            new_slot = DBSlotDefinition(**slot_data)
            db.add(new_slot)
            created_count += 1
            print(f"  创建系统词槽: {slot_config['slot_name']} ({slot_config['slot_name_en']})")
    
    return created_count, updated_count


def init_all_system_slots():
    """为所有指令库初始化系统词槽"""
    # 确保数据库表已创建
    create_new_tables()
    
    # 获取数据库会话
    db = next(get_new_db())
    
    try:
        # 获取所有指令库
        libraries = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.is_active == True
        ).all()
        
        if not libraries:
            print("没有找到活跃的指令库")
            return
        
        total_created = 0
        total_updated = 0
        
        for library in libraries:
            print(f"\n正在为指令库 '{library.name}' (ID: {library.id}) 初始化系统词槽...")
            created, updated = init_system_slots_for_library(db, library.id)
            total_created += created
            total_updated += updated
        
        # 提交事务
        db.commit()
        
        print(f"\n系统词槽初始化完成:")
        print(f"  处理指令库数量: {len(libraries)}")
        print(f"  创建系统词槽: {total_created}")
        print(f"  更新系统词槽: {total_updated}")
        
    except Exception as e:
        db.rollback()
        print(f"初始化系统词槽失败: {str(e)}")
        raise
    finally:
        db.close()


def add_system_slots_to_library(library_id: int):
    """为指定指令库添加系统词槽"""
    db = next(get_new_db())
    
    try:
        # 验证指令库是否存在
        library = db.query(DBInstructionLibraryMaster).filter(
            DBInstructionLibraryMaster.id == library_id
        ).first()
        
        if not library:
            print(f"指令库 ID {library_id} 不存在")
            return False
        
        print(f"正在为指令库 '{library.name}' (ID: {library.id}) 添加系统词槽...")
        created, updated = init_system_slots_for_library(db, library_id)
        
        db.commit()
        
        print(f"系统词槽添加完成:")
        print(f"  创建: {created}")
        print(f"  更新: {updated}")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"添加系统词槽失败: {str(e)}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 为指定指令库添加系统词槽
        try:
            library_id = int(sys.argv[1])
            add_system_slots_to_library(library_id)
        except ValueError:
            print("请提供有效的指令库ID")
    else:
        # 为所有指令库初始化系统词槽
        init_all_system_slots() 