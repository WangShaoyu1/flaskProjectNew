#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TensorFlow 2.12.0 NoneType错误修复脚本

修复TensorFlow 2.12.0中的array_ops.py文件中的NoneType错误
错误: TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'
"""

import os
import sys
import shutil
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_tensorflow_path():
    """查找TensorFlow安装路径"""
    try:
        import tensorflow as tf
        tf_path = tf.__file__
        tf_dir = os.path.dirname(tf_path)
        array_ops_path = os.path.join(tf_dir, 'python', 'ops', 'array_ops.py')
        
        if os.path.exists(array_ops_path):
            return array_ops_path
        else:
            logger.error(f"未找到array_ops.py文件: {array_ops_path}")
            return None
    except ImportError:
        logger.error("TensorFlow未安装")
        return None

def backup_file(file_path):
    """备份原始文件"""
    backup_path = file_path + '.backup'
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        logger.info(f"已备份原始文件: {backup_path}")
    else:
        logger.info(f"备份文件已存在: {backup_path}")

def fix_array_ops_file(file_path):
    """修复array_ops.py文件中的NoneType错误"""
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找问题行
        problem_line = 'listdiff.__doc__ = gen_array_ops.list_diff.__doc__ + "\\n" + listdiff.__doc__'
        
        if problem_line in content:
            logger.info("找到问题行，正在修复...")
            
            # 修复方案：添加空值检查
            fixed_line = '''# 修复NoneType错误
if gen_array_ops.list_diff.__doc__ is not None and listdiff.__doc__ is not None:
    listdiff.__doc__ = gen_array_ops.list_diff.__doc__ + "\\n" + listdiff.__doc__
elif gen_array_ops.list_diff.__doc__ is not None:
    listdiff.__doc__ = gen_array_ops.list_diff.__doc__
elif listdiff.__doc__ is not None:
    listdiff.__doc__ = listdiff.__doc__
else:
    listdiff.__doc__ = "List difference operation"'''
            
            # 替换内容
            content = content.replace(problem_line, fixed_line)
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("✅ 修复完成！")
            return True
        else:
            logger.info("未找到问题行，可能已经修复或版本不同")
            return False
            
    except Exception as e:
        logger.error(f"修复失败: {e}")
        return False

def restore_backup(file_path):
    """恢复备份文件"""
    backup_path = file_path + '.backup'
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, file_path)
        logger.info("已恢复原始文件")
        return True
    else:
        logger.error("备份文件不存在")
        return False

def main():
    """主函数"""
    print("🔧 TensorFlow 2.12.0 NoneType错误修复工具")
    print("=" * 50)
    
    # 查找TensorFlow路径
    array_ops_path = find_tensorflow_path()
    if not array_ops_path:
        return 1
    
    logger.info(f"找到array_ops.py文件: {array_ops_path}")
    
    # 检查是否有写权限
    if not os.access(array_ops_path, os.W_OK):
        logger.error("没有写权限，请以管理员身份运行")
        return 1
    
    # 备份原始文件
    backup_file(array_ops_path)
    
    # 修复文件
    if fix_array_ops_file(array_ops_path):
        print("\\n🎉 修复成功！现在可以尝试启动Rasa服务")
        print("如果遇到问题，可以运行以下命令恢复:")
        print(f"python {__file__} --restore")
    else:
        print("\\n⚠️  修复失败或不需要修复")
    
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--restore':
        # 恢复模式
        array_ops_path = find_tensorflow_path()
        if array_ops_path:
            restore_backup(array_ops_path)
    else:
        # 修复模式
        sys.exit(main()) 