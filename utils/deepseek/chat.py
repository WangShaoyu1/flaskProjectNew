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
    root.withdraw()
    root.attributes('-topmost', True)

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
    try:
        client = OpenAI(api_key="sk-c2756c6b7267452e9880739d8f0da054", base_url="https://api.deepseek.com")
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

    # 生成带时间戳的输出路径
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    output_dir = os.path.join(os.path.dirname(input_file_path), "output")
    os.makedirs(output_dir, exist_ok=True)

    # ================== 新增功能开始 ==================
    # 生成并保存基础处理结果
    txt_system_prompt = "如下内容，不要修改已有的文本，你只负责断句，加上标点符号，同时按照word文档段落层次分好段落"
    txt_result = generate_content(txt_system_prompt, input_content)

    if not txt_result:
        logging.error("TXT内容生成失败，终止处理流程")
        return

    # 保存基础处理结果（带时间戳）
    txt_output_path = os.path.join(output_dir, f"{base_name}_processed_{timestamp}.txt")
    if write_to_file(txt_result, txt_output_path):
        logging.info(f"中间文件保存成功: {txt_output_path}")
    else:
        logging.error("中间文件保存失败")
        return

    # 生成结构化MD文档（基于处理后的文本）
    md_prompt = """你是一个专业文档编辑助手，请将以下的文本转换为结构清晰的Word格式的文档：
    - 只整理格式，不修改内容，仅少量总结内容
    - 关键信息使用**加粗**或*斜体*强调
    - 保持word排版风格
    - 保持朴实的小说文风、细节丰富、饱含感情，娓娓道来、宏大叙事，不要AI味
    - 口语化表达，少量的正式、专业表达  
    - 整体原有的文字改动不超过5%，输出的文本长度和输入的文本长度保持一致，保持输入文字的原意
    """

    md_result = generate_content(md_prompt, txt_result)  # 改 为使用处理后的文本
    # ================== 新增功能结束 ==================

    # 保存最终结果（带时间戳）
    if md_result:
        md_output_path = os.path.join(output_dir, f"{base_name}_structured_{timestamp}.docx")
        if write_to_file(md_result, md_output_path):
            logging.info(f"MD文件生成成功: {md_output_path}")
            # 控制台输出双路径
            print(f"\n生成结果已保存至:\nTXT文件: {txt_output_path}\nMD文件: {md_output_path}")
        else:
            logging.error("MD文件保存失败")
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

        if not input_path.lower().endswith('.txt'):
            logging.error("非文本文件类型")
            print("错误：仅支持.txt文件")
        else:
            process_file(input_path)

    except Exception as e:
        logging.exception("发生未捕获的异常:")
        print(f"程序异常: {str(e)}")
