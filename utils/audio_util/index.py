import os
import random
from pydub import AudioSegment
import time
from concurrent.futures import ThreadPoolExecutor


def process_audio_combination(file1, file2, silence, output_folder):
    """
    单独处理两个音频的合并和输出
    """
    try:
        audio1 = AudioSegment.from_file(file1)  # 自动识别格式
        audio2 = AudioSegment.from_file(file2)  # 自动识别格式
        file1_name = os.path.basename(file1)[:11]  # 第一组文件名前 11 位
        file2_name = os.path.basename(file2).replace('.mp3', '.wav')  # 第二组文件名

        combined = audio1 + silence + audio2
        output_file_name = f"{file1_name}_{file2_name}"
        output_path = os.path.join(output_folder, output_file_name)
        combined.export(output_path, format="wav")
        print(f"Generated: {output_file_name}")
    except Exception as e:
        print(f"Error processing {file1} and {file2}: {e}")


def generate_combinations_with_silence_multithreaded(folder1, folder2, output_folder, silence_duration_ms=1000,
                                                     max_workers=4):
    """
    多线程实现音频组合
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    folder1_files = [os.path.join(folder1, f) for f in os.listdir(folder1) if f.lower().endswith(('.mp3', '.wav'))]
    folder2_files = [os.path.join(folder2, f) for f in os.listdir(folder2) if f.lower().endswith(('.mp3', '.wav'))]

    print("Folder1 files (wav):", folder1_files)
    print("Folder2 files (mp3):", folder2_files)

    if not folder1_files or not folder2_files:
        print("文件夹中没有符合条件的音频文件！")
        return

    silence = AudioSegment.silent(duration=silence_duration_ms)
    start_time = time.time()

    # 使用多线程处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for file1 in folder1_files:
            for file2 in folder2_files:
                executor.submit(process_audio_combination, file1, file2, silence, output_folder)

    total_time = time.time() - start_time
    print(f"多线程生成完成，保存到 {output_folder}")
    print(f"总处理时长：{total_time:.2f} seconds")


def generate_random_combinations(output_folder, final_output_folder, sample_size=100):
    """
    从生成的音频文件中随机选择一定数量保存到新目录。
    """
    if not os.path.exists(final_output_folder):
        os.makedirs(final_output_folder)

    # 获取所有已生成的文件
    all_files = [os.path.join(output_folder, f) for f in os.listdir(output_folder) if
                 f.lower().endswith(('.mp3', '.wav'))]

    # 检查文件数量是否足够
    if len(all_files) < sample_size:
        print(f"可用文件不足！总共有 {len(all_files)} 个文件，但需要 {sample_size} 个")
        return

    # 随机选择指定数量的文件
    selected_files = random.sample(all_files, sample_size)

    # 保存随机选择的文件到新目录
    for file in selected_files:
        output_path = os.path.join(final_output_folder, os.path.basename(file))
        os.rename(file, output_path)

    print(f"随机选取了 {len(selected_files)} 个音频文件，保存到 {final_output_folder}")


if __name__ == "__main__":
    # 配置路径和参数
    folder1 = r"D:\语音测试1127\小万小万-测试集"  # wav 文件夹
    folder2 = r"D:\语音测试1127\识别率测试音频"  # mp3 文件夹
    output_folder = r"D:\语音测试1127\output_latest"  # 所有组合音频输出路径
    final_output_folder = r"D:\语音测试1127\random"  # 随机选择后的音频保存路径

    silence_duration_ms = 600  # 空白音频时长（毫秒）
    max_workers = 24  # 多线程数
    sample_size = 100  # 随机选择的音频数量

    # 1. 多线程生成所有组合音频
    generate_combinations_with_silence_multithreaded(folder1, folder2, output_folder, silence_duration_ms,
                                                     max_workers)

    # 2. 从生成的音频中随机选择指定数量
    generate_random_combinations(output_folder, final_output_folder, sample_size)
