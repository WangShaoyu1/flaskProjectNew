import time

import cv2
import os
import numpy as np
import pytesseract
import shutil

# 支持的图片格式扩展
SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}


def is_image_supported(file_path):
    """检查文件是否是支持的图片格式"""
    _, ext = os.path.splitext(file_path)
    return ext.lower() in SUPPORTED_FORMATS


def read_log(log_path):
    """读取日志文件，返回已处理图片的列表"""
    if not os.path.exists(log_path):
        return set()  # 如果没有日志文件，返回空集合

    with open(log_path, 'r') as log_file:
        processed_files = {line.strip() for line in log_file}
    return processed_files


def write_log(log_path, file_path):
    """将处理过的图片路径写入日志文件"""
    with open(log_path, 'a') as log_file:
        log_file.write(f"{file_path}\n")


def process_image(image_path, output_path):
    """去除水印的主要处理函数"""
    # 读取图像
    image = cv2.imread(image_path)

    if image is None:
        print(f"无法读取图像: {image_path}")
        return

    # 转换为灰度图像
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)

    # 使用修复算法去除水印
    result = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

    # 确保输出路径有效
    if result is None:
        print(f"处理后的图像无效: {image_path}")
        return

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # 创建目录

    # 尝试写入文件，并检查返回值
    success = cv2.imwrite(output_path, result)
    if not success:
        print(f"无法写入文件: {output_path}")
    else:
        print(f"处理完成并保存到: {output_path}")


def remove_watermark(image_path, output_path):
    """去除指定区域的水印"""
    # 读取图像
    image = cv2.imread(image_path)
    if image is None:
        print(f"无法读取图像: {image_path}")
        return

    height, width = image.shape[:2]

    # 假设水印通常位于右下角的 20% 区域
    x1, y1 = int(width * 0.8), int(height * 0.8)
    x2, y2 = width, height

    # 创建掩膜
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.rectangle(mask, (x1, y1), (x2, y2), (255), thickness=cv2.FILLED)

    # 使用修复算法去除水印
    result = cv2.inpaint(image, mask, inpaintRadius=1, flags=cv2.INPAINT_TELEA)

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 尝试写入文件，并检查返回值
    success = cv2.imwrite(output_path, result)
    if not success:
        print(f"无法写入文件: {output_path}")
    else:
        print(f"处理完成并保存到: {output_path}")


def process_images_in_directory(directory, output_dir, log_path):
    """处理文件夹中的所有图片"""
    processed_files = read_log(log_path)

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)

            # 检查图片格式是否支持，且图片是否已处理
            if is_image_supported(file_path) and file_path not in processed_files:
                output_path = os.path.join(output_dir, os.path.basename(file_path))

                # 执行水印去除操作
                remove_watermark(file_path, output_path)

                # 将处理过的文件记录到日志中
                # write_log(log_path, file_path)
            else:
                print(f"跳过文件: {file_path} (已处理或不支持)")


def process_input(input_path, output_dir, log_path):
    """根据输入类型处理单个文件或整个文件夹"""
    if os.path.isfile(input_path):
        # 如果是单个文件，检查是否已处理
        processed_files = read_log(log_path)
        if is_image_supported(input_path) and input_path not in processed_files:
            output_path = os.path.join(output_dir, os.path.basename(input_path))
            remove_watermark(input_path, output_path)
            write_log(log_path, input_path)
        else:
            print(f"文件已处理或不支持: {input_path}")
    elif os.path.isdir(input_path):
        # 如果是文件夹，处理文件夹中的所有文件
        process_images_in_directory(input_path, output_dir, log_path)
    else:
        print(f"无效的输入路径: {input_path}")

    # 所有处理完成后，复制处理后的文件到原文件夹
    copy_processed_images(output_dir, input_path)


def copy_processed_images(output_dir, input_path):
    time.sleep(10)
    """将处理后的文件复制到原文件目录"""
    for file_name in os.listdir(output_dir):
        src_file = os.path.join(output_dir, file_name)
        dest_file = os.path.join(input_path, file_name)

        # 只复制文件，不复制目录
        if os.path.isfile(src_file):
            shutil.copy2(src_file, dest_file)
            print(f"已复制处理后的文件到: {dest_file}")


# 使用示例
input_path = 'D:\\gitlab\\myBlogPaperMod\\static\\images\\juejin\\'  # 可以是文件或文件夹
output_dir = 'D:\\gitlab\\myBlogPaperMod\\static\\images\\images_juejin_covert\\'  # 处理后的图片保存目录
log_path = 'D:\\gitlab\\myBlogPaperMod\\static\\images\\juejin\\processed_url.txt'  # 已处理文件的记录日志

process_input(input_path, output_dir, log_path)
