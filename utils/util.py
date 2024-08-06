import json
import os
import stat
import platform


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

        # 检查文件是否存在，不存在则创建
        if not os.path.exists(abs_file_path):
            with open(abs_file_path, 'w') as f:
                pass  # 创建空文件

        # 检查写入权限
        if not os.access(abs_file_path, os.W_OK):
            print(f"文件不可写入：{abs_file_path},正在尝试修改权限。")
            # 尝试修改文件权限
            try:
                grant_write_access(abs_file_path)
            except Exception as e:
                print(f"无法修改文件权限：{abs_file_path} - {e}")
                return

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
        # 如果输入是字符串，则尝试解析为Python对象
        if isinstance(raw_data, str):
            raw_data = raw_data.replace("'", '"')
            raw_data = json.loads(raw_data)  # 使用json.loads解析JSON字符串

        # 处理不同类型的 JSON 数据
        if isinstance(raw_data, list):
            # 如果是列表，则逐行格式化每个元素
            formatted_data = '\n'.join(json.dumps(item, ensure_ascii=False) for item in raw_data)
            return f'[\n{formatted_data}\n]'
        elif isinstance(raw_data, dict):
            # 如果是字典，则格式化整个字典
            formatted_data = json.dumps(raw_data, ensure_ascii=False, indent=4)
            return formatted_data
        else:
            raise ValueError("输入数据不是有效的JSON格式")
    except Exception as e:
        print(f"格式化数据时出错: {e}")
        return None


def grant_write_access(file_path):
    """授予当前用户对文件的写入权限"""
    if platform.system() == 'Windows':
        import ntsecuritycon as con
        import win32security
        user, domain, type = win32security.LookupAccountName("", os.getlogin())
        sd = win32security.GetFileSecurity(file_path, win32security.DACL_SECURITY_INFORMATION)
        dacl = sd.GetSecurityDescriptorDacl()
        new_dacl = win32security.ACL()
        if dacl:
            for i in range(dacl.GetAceCount()):
                new_dacl.AddAce(*dacl.GetAce(i))
        new_dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_GENERIC_WRITE, user)
        sd.SetSecurityDescriptorDacl(1, new_dacl, 0)
        win32security.SetFileSecurity(file_path, win32security.DACL_SECURITY_INFORMATION, sd)
        print(f"已授予用户 {os.getlogin()} 对文件 {file_path} 的写权限")
    elif platform.system() == 'Linux':
        # 对于Linux系统，使用os.chmod授予写权限
        try:
            os.chmod(file_path, stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            print(f"已授予用户对文件 {file_path} 的写权限")
        except Exception as e:
            print(f"授予写权限时出错: {e}")
