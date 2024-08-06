import shutil
from utils.iflytek.image_reg import *
from utils.iflytek.image_compression import *

Input_folder = fr"D:\gitlab\flaskProjectNew\app\static\img\Pictures"
Output_folder = fr"D:\gitlab\flaskProjectNew\app\static\img\crop"


def process_image(input_path, crop_path, output_path, max_size_kb=800):
    # 裁剪人像
    crop_face(input_path, crop_path)

    # 压缩图像
    compress_image(crop_path, output_path, max_size_kb)


def process_images_in_folder(input_folder, output_folder, max_size_kb=800):
    # 清空或创建输出文件夹
    clear_or_create_folder(output_folder)

    # 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_folder):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            continue

        input_path = os.path.join(input_folder, filename)
        cropped_path = os.path.join(output_folder, f"cropped_{filename}")
        output_path = os.path.join(output_folder, f"compressed_{filename}")

        if crop_face(input_path, cropped_path):
            compress_image(cropped_path, output_path, max_size_kb)
            print(f"Processed {filename} and saved to {output_path}")
        else:
            print(f"Failed to process {filename}")


def clear_or_create_folder(folder_path):
    # 如果文件夹存在，清空其中内容
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    # 重新创建文件夹
    os.makedirs(folder_path)


process_images_in_folder(Input_folder, Output_folder)
