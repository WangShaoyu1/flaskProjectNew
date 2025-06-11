import logging
import os
import wave

import numpy as np
from pydub import AudioSegment

# 设置日志
logging.basicConfig(level=logging.INFO)


def calculate_dynamic_threshold(samples, silence_factor=0.5):
    """计算动态静音阈值"""
    rms = np.sqrt(np.mean(np.square(samples)))  # 计算均方根（RMS）值
    threshold = rms * silence_factor  # 根据调整因子计算静音阈值
    logging.info(f"RMS: {rms}, Silence Threshold: {threshold}")  # 输出RMS和静音阈值
    return threshold


def detect_silence_in_audio(audio_file, silence_threshold, min_silence_len, chunk_size=10):
    """
    检测音频中的静音段
    :param audio_file: 输入的音频文件
    :param silence_threshold: 静音阈值，单位 dBFS
    :param min_silence_len: 静音段最短时长，单位毫秒
    :param chunk_size: 每次取的音频片段大小，单位毫秒
    :return: 静音段的列表，包含每个静音段的起始和结束时间（单位毫秒）
    """
    # 获取文件扩展名
    file_extension = os.path.splitext(audio_file)[1].lower()

    # 根据文件格式加载音频文件
    if file_extension == '.wav':
        audio = AudioSegment.from_wav(audio_file)
    elif file_extension == '.mp3':
        audio = AudioSegment.from_mp3(audio_file)
    else:
        raise ValueError(f"不支持的音频格式: {file_extension}. 仅支持 .wav 和 .mp3 格式")

    silent_periods = []
    silence_start = None
    silence_duration = 0

    for i in range(0, len(audio), chunk_size):
        # 每次取 chunk_size 毫秒的音频片段
        sample = audio[i:i + chunk_size]  # 获取当前片段
        rms = sample.rms  # 计算rms值

        # 打印每一段的 rms 值与其起始位置
        # logging.info(f"片段 {i}-{i + chunk_size}ms, RMS: {rms}")

        # 如果当前片段为静音片段，累加静音时长
        if rms < silence_threshold:
            if silence_start is None:  # 如果没有开始静音段
                silence_start = i
                # logging.info(f"静音开始，起始位置: {silence_start}ms")
            silence_duration += chunk_size  # 累加静音时长
        else:
            if silence_start is not None and silence_duration > 0:
                silence_end = i
                logging.info(f"静音段起始于: {silence_start}ms to {silence_end}ms，持续时长: {silence_duration}ms")
                if silence_duration >= min_silence_len:
                    silent_periods.append((silence_start, silence_end))
                silence_start = None  # 重置静音段起始
                silence_duration = 0  # 重置静音段时长

    # 处理音频结束后仍然存在的静音段
    if silence_start is not None and silence_duration > 0:
        silence_end = len(audio)
        logging.info(f"静音段结束，结束位置: {silence_end}ms，持续时长: {silence_duration}ms")

        if silence_duration >= min_silence_len:
            silent_periods.append((silence_start, silence_end))

    return silent_periods


def process_single_audio(input_file, output_folder, silence_threshold=-40, silence_factor=0.5, min_silence_len=500):
    """处理单个音频文件，检测静音段并保存结果"""

    # 检测音频中的静音段
    silent_periods = detect_silence_in_audio(input_file, silence_threshold, min_silence_len)

    # 打印检测到的静音段
    if silent_periods:
        logging.info(f"静音段：{silent_periods}")
        logging.info(f"检测到 {len(silent_periods)} 个静音段")
    else:
        logging.info("未检测到静音段")

    # 读取音频
    file_extension = os.path.splitext(input_file)[1].lower()
    if file_extension == '.wav':
        audio = AudioSegment.from_wav(input_file)
    elif file_extension == '.mp3':
        audio = AudioSegment.from_mp3(input_file)

    # 截取掉静音片段
    non_silent_audio = AudioSegment.empty()
    last_end = 0
    for start, end in silent_periods:
        non_silent_audio += audio[last_end:start]
        last_end = end
    non_silent_audio += audio[last_end:]

    # 保存去除静音片段后的音频
    output_file = os.path.join(output_folder,
                               f"{os.path.basename(input_file).replace('.mp3', '').replace('.wav', '')}_no_silence{file_extension}")
    non_silent_audio.export(output_file, format=file_extension[1:])
    logging.info(f"去除静音片段后的音频已保存至: {output_file}")

    # 保存静音段数据到文件
    output_file = os.path.join(output_folder, f"{os.path.basename(input_file)}_silence_periods.txt")
    output_file_txt = os.path.join(output_folder, "all_silence_periods.txt")
    with open(output_file_txt, 'a') as f:
        f.write(f"-----------{os.path.basename(input_file)}-----------\n")
        for start, end in silent_periods:
            f.write(f"Start: {start}, End: {end}, Duration: {end - start} ms\n")

    logging.info(f"静音段数据已保存至: {output_file}")


def process_audio_folder(input_folder, output_folder, silence_threshold=-40, silence_factor=0.5, min_silence_len=500):
    """处理文件夹中的所有音频文件"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 遍历文件夹中的所有音频文件
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)

        if os.path.isfile(file_path) and (file_path.endswith(".mp3") or file_path.endswith(".wav")):
            logging.info(f"开始处理文件: {file_path}")
            process_single_audio(file_path, output_folder, silence_threshold, silence_factor, min_silence_len)


# 示例使用
def main():
    input_folder_1 = r"D:\语音测试1127\小万小万-测试集"  # 第一组音频文件夹路径
    input_folder_2 = r"D:\语音测试1127\识别率测试音频"  # 第二组音频文件夹路径
    output_folder_1 = r"D:\语音测试1127\cutted\小万小万"  # 输出文件夹路径
    output_folder_2 = r"D:\语音测试1127\cutted\识别率测试音频"  # 输出文件夹路径

    if not os.path.exists(output_folder_1):
        os.makedirs(output_folder_1)
    if not os.path.exists(output_folder_2):
        os.makedirs(output_folder_2)

    # 调整参数：更高的灵敏度和更短的静音段时长
    silence_factor = 0.6  # 增加灵敏度
    min_silence_len = 100  # 缩短最短静音段长度
    silence_threshold = 120  # 静音阈值

    # 处理单个音频文件
    process_single_audio(r"D:\语音测试1127\识别率测试音频\14-查看设备详细信息-女.mp3", r"D:\语音测试1127\abc",
                         silence_threshold=silence_threshold,
                         silence_factor=silence_factor,
                         min_silence_len=min_silence_len)

    # 处理第一组文件夹中的音频
    process_audio_folder(input_folder_1, output_folder_1, silence_threshold, silence_factor, min_silence_len)

    # 处理第二组文件夹中的音频
    process_audio_folder(input_folder_2, output_folder_2, silence_threshold, silence_factor, min_silence_len)


if __name__ == "__main__":
    main()
