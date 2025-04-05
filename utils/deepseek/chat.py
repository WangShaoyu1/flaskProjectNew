import os
import logging
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from openai import OpenAI

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("processing.log")
    ]
)


def select_file():
    """弹出系统文件选择对话框"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    root.attributes('-topmost', True)  # 确保窗口置顶

    file_path = filedialog.askopenfilename(
        title="选择要处理的文本文件",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    root.destroy()
    return file_path


def read_txt_file(file_path):
    """读取指定路径的txt文件内容"""
    logging.info(f"开始读取文件: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            logging.info(f"成功读取文件，字符数: {len(content)}")
            return content
    except Exception as e:
        logging.error(f"文件读取失败: {str(e)}")
        return None


def generate_content(system_prompt, user_content):
    """调用API生成内容"""
    logging.info("正在调用API生成内容...")
    logging.debug(f"系统提示: {system_prompt[:50]}...")  # 截短长文本
    logging.debug(f"用户内容: {user_content[:100]}...")

    try:
        client = OpenAI(api_key="sk-4ad51255d1974fe68da91d6a8a8b4b35", base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            stream=False
        )
        logging.info("API调用成功，生成内容完成")
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"API调用失败: {str(e)}")
        return None


def write_to_file(content, output_path):
    """将内容写入指定路径"""
    logging.info(f"准备写入文件: {output_path}")
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(content)
        logging.info(f"文件写入成功，字节数: {len(content.encode('utf-8'))}")
        return True
    except Exception as e:
        logging.error(f"文件写入失败: {str(e)}")
        return False


def process_file(input_file_path):
    """处理文件的主流程"""
    start_time = datetime.now()
    logging.info(f"\n{'=' * 40}\n开始处理文件: {input_file_path}")

    # 读取原始文件
    input_content = read_txt_file(input_file_path)
    if not input_content:
        logging.warning("文件内容为空，终止处理流程")
        return

    # 获取基础文件名
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]

    # 生成并保存txt结果
    txt_system_prompt = "如下内容，不要修改已有的文本，你只负责短句，加上标点符号，同时分好段落"
    logging.info("开始生成TXT版本...")
    if txt_result := generate_content(txt_system_prompt, input_content):
        txt_output_path = os.path.join(
            os.path.dirname(input_file_path),
            "results",
            f"{base_name}_processed.txt"
        )
        if write_to_file(txt_result, txt_output_path):
            logging.info(f"TXT文件生成成功: {txt_output_path}")
        else:
            logging.error("TXT文件生成失败")
    else:
        logging.error("TXT内容生成失败，跳过后续处理")
        return

    # 生成并保存md结果
    md_system_prompt = "简单美化下文章，略带商业文风，口语多一些，可以带点脏字，整体改动不能超过10%。并将txt格式修改成md格式，并加粗一些文字。"
    # md_system_prompt = "不改变原文，将txt格式修改成md格式，并加粗一些文字。"
    logging.info("开始生成MD版本...")
    if md_result := generate_content(md_system_prompt, txt_result):
        md_output_path = os.path.join(
            os.path.dirname(input_file_path),
            "results",
            f"{base_name}_processed.md"
        )
        if write_to_file(md_result, md_output_path):
            logging.info(f"MD文件生成成功: {md_output_path}")
        else:
            logging.error("MD文件生成失败")
    else:
        logging.error("MD内容生成失败")

    # 记录处理时长
    duration = datetime.now() - start_time
    logging.info(f"处理完成，总耗时: {duration.total_seconds():.2f}秒\n{'=' * 40}\n")


if __name__ == "__main__":
    try:
        logging.info("启动文件选择对话框...")
        input_path = select_file()

        if not input_path:
            logging.warning("用户取消文件选择")
            print("操作已取消")
            exit(0)

        logging.info(f"用户选择文件: {input_path}")

        # 验证文件有效性
        if not os.path.isfile(input_path):
            logging.error("无效文件路径")
            print("错误：文件不存在")
        elif not input_path.lower().endswith('.txt'):
            logging.error("非文本文件类型")
            print("错误：仅支持.txt文件")
        else:
            process_file(input_path)
            print("文件处理完成！")

    except Exception as e:
        logging.exception("发生未捕获的异常:")
        print(f"程序异常: {str(e)}")
