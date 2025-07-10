"""
数据库迁移脚本：为slot_definitions表添加is_system字段
"""

import sqlite3
import sys
import os

# 数据库文件路径
DB_PATH = "instruction_platform_new.db"

def migrate_add_is_system():
    """添加is_system字段到slot_definitions表"""
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查is_system字段是否已存在
        cursor.execute("PRAGMA table_info(slot_definitions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_system' not in columns:
            print("添加is_system字段到slot_definitions表...")
            
            # 添加is_system字段，默认值为0(False)
            cursor.execute("""
                ALTER TABLE slot_definitions 
                ADD COLUMN is_system BOOLEAN DEFAULT 0
            """)
            
            # 提交更改
            conn.commit()
            print("is_system字段添加成功")
            
            # 验证字段是否添加成功
            cursor.execute("PRAGMA table_info(slot_definitions)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"当前slot_definitions表的字段: {columns}")
            
        else:
            print("is_system字段已存在，无需添加")
        
        # 关闭连接
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"数据库迁移失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始数据库迁移...")
    success = migrate_add_is_system()
    
    if success:
        print("数据库迁移完成")
    else:
        print("数据库迁移失败")
        sys.exit(1) 