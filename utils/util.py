import os
import stat
import json


def write_to_file(file_path, data, need_json=False):
    try:
        if need_json:
            # 格式化数据
            formatted_data = format_json_lines(data)
            if not formatted_data:
                raise ValueError("数据格式化失败")
        else:
            formatted_data = data
            
        # 使用绝对路径
        abs_file_path = os.path.abspath(file_path)

        # 检查目录是否存在，不存在则创建
        directory = os.path.dirname(abs_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        # 检查写入权限
        if not os.access(abs_file_path, os.W_OK):
            print(f"文件不可写入：{abs_file_path},正在尝试修改权限。")
            # 修改文件权限为可写
            os.chmod(abs_file_path, stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
            if not os.access(abs_file_path, os.W_OK):
                raise PermissionError(f"无法修改文件权限：{abs_file_path}")

        # 打开文件并写入数据
        with open(abs_file_path, 'a') as f:
            f.write(formatted_data)
            print(f"数据已成功写入 {abs_file_path}")

    except PermissionError as pe:
        print(f"写入文件时出错: 权限不足 - {pe}")
    except FileNotFoundError as fnfe:
        print(f"写入文件时出错: 找不到文件或目录 - {fnfe}")
    except IsADirectoryError as iade:
        print(f"写入文件时出错: 目标是一个目录，不能写入文件 - {iade}")
    except OSError as oe:
        print(f"写入文件时出错: 操作系统错误 - {oe}")
    except Exception as e:
        print(f"写入文件时出错: 未知错误 - {e}")


def format_json_lines(raw_data):
    """将原始数据格式化为每个条目占一行的JSON格式"""
    try:
        # 确保输入是列表
        if isinstance(raw_data, str):
            # 如果是字符串，尝试解析为Python对象
            raw_data = eval(raw_data)
        formatted_data = '\n'.join(json.dumps(item, ensure_ascii=False) for item in raw_data)
        return f'[\n{formatted_data}\n]'
    except Exception as e:
        print(f"格式化数据时出错: {e}")
        return None
