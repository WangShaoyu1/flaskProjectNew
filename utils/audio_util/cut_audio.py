import os
import re
import subprocess
import numpy as np

# 设置文件夹路径
folder1 = r"D:\语音测试1127\小万小万-测试集C"  # wav 文件夹
folder2 = r"D:\语音测试1127\识别率测试音频C"  # mp3 文件夹
output_folder1_silence = r"D:\语音测试1127\output_folder1_silence"  # 第一组音频的第二段环境音输出路径
output_folder2_silence = r"D:\语音测试1127\output_folder2_silence"  # 第二组音频的第一段环境音输出路径

# 静音时长阈值，单位为秒
silence_threshold = -50  # 静音阈值（dB），用于判定是否为环境音


# 获取文件夹内所有音频文件
def get_audio_files(folder, ext):
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(ext)]


# 计算音频的静音部分长度，返回静音时长（单位：秒）
def get_silence_duration(file, threshold=-50, is_second_silence=False):
    """
    获取音频文件中的静音时长，返回静音的持续时间（单位：秒）。
    :param file: 音频文件路径
    :param threshold: 静音阈值，单位为 dB
    :param is_second_silence: 是否为第二段环境音的处理
    :return: 静音时长（秒）
    """
    # 使用ffmpeg的silencedetect来检测静音部分
    cmd = [
        "ffmpeg", "-i", file,
        "-af", f"silencedetect=n={silence_threshold}dB:d=1",  # 使用传入的静音阈值
        "-f", "null", "-"
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
                                encoding='utf-8')

        # 检查stderr是否为空
        stderr_output = result.stderr
        if stderr_output:
            duration_lines = []
            for line in stderr_output.splitlines():
                if 'silence_end' in line:
                    duration_lines.append(line)

            silence_duration = 0
            for line in duration_lines:
                # 从stderr输出中提取时间（可以根据实际输出调整正则或解析方式）
                match = re.search(r"silence_end: (\d+(\.\d+)?)", line)
                if match:
                    print(f"silence_end: {match.group(1)}")
                    silence_duration = float(match.group(1)) * 1000  # 转换为毫秒
                    break

            if silence_duration == 0:
                print(f"Warning: No silence detected in {file}")
            return silence_duration
        else:
            print(f"Error: ffmpeg stderr is empty for {file}")
            return 0  # 处理错误的情况
    except Exception as e:
        print(f"Error while processing {file}: {str(e)}")
        return 0


# 提取并保存第二段环境音（第一组音频）
def extract_second_silence_from_file(file, output_folder):
    silence_duration = get_silence_duration(file, is_second_silence=True)
    output_filename = os.path.join(output_folder, os.path.basename(file))

    if silence_duration > 0:
        # 通过ffmpeg提取第二段静音部分并保存为新的文件
        cmd = [
            'ffmpeg', '-i', file,
            '-ss', str(silence_duration),  # 跳过前面的音频，提取后段环境音
            output_filename
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return silence_duration


# 提取并保存第一段环境音（第二组音频）
def extract_first_silence_from_file(file, output_folder):
    silence_duration = get_silence_duration(file, is_second_silence=False)
    output_filename = os.path.join(output_folder, os.path.basename(file))

    if silence_duration > 0:
        # 通过ffmpeg提取第一段静音部分并保存为新的文件
        cmd = [
            'ffmpeg', '-i', file,
            '-t', str(silence_duration),  # 提取文件的前段环境音
            output_filename
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return silence_duration


# 处理第一组音频，提取第二段环境音
def process_first_group_files(folder1_files, output_folder1):
    if not os.path.exists(output_folder1):
        os.makedirs(output_folder1)

    silence_durations = []  # 存储第二段环境音的时长
    for file in folder1_files:
        print(f"正在处理第一组音频文件：{os.path.basename(file)}")
        silence_duration = extract_second_silence_from_file(file, output_folder1)
        silence_durations.append(silence_duration)

    # 打印第二段环境音的统计数据
    avg_silence = np.mean(silence_durations)
    max_silence = np.max(silence_durations)
    min_silence = np.min(silence_durations)
    median_silence = np.median(silence_durations)

    print(f"第一组音频（第二段环境音）时长统计:")
    print(f"平均时长: {avg_silence * 1000:.2f}ms")
    print(f"最大时长: {max_silence * 1000:.2f}ms")
    print(f"最小时长: {min_silence * 1000:.2f}ms")
    print(f"中位数时长: {median_silence * 1000:.2f}ms")

    # 保存统计数据
    with open(os.path.join(output_folder1, "second_silence_durations.txt"), 'w') as f:
        for silence in silence_durations:
            f.write(f"{silence * 1000:.2f}\n")


# 处理第二组音频，提取第一段环境音
def process_second_group_files(folder2_files, output_folder2):
    if not os.path.exists(output_folder2):
        os.makedirs(output_folder2)

    silence_durations = []  # 存储第一段环境音的时长
    for file in folder2_files:
        print(f"正在处理第二组音频文件：{os.path.basename(file)}")
        silence_duration = extract_first_silence_from_file(file, output_folder2)
        silence_durations.append(silence_duration)

    # 打印第一段环境音的统计数据
    avg_silence = np.mean(silence_durations)
    max_silence = np.max(silence_durations)
    min_silence = np.min(silence_durations)
    median_silence = np.median(silence_durations)

    print(f"第二组音频（第一段环境音）时长统计:")
    print(f"平均时长: {avg_silence * 1000:.2f}ms")
    print(f"最大时长: {max_silence * 1000:.2f}ms")
    print(f"最小时长: {min_silence * 1000:.2f}ms")
    print(f"中位数时长: {median_silence * 1000:.2f}ms")

    # 保存统计数据
    with open(os.path.join(output_folder2, "first_silence_durations.txt"), 'w') as f:
        for silence in silence_durations:
            f.write(f"{silence * 1000:.2f}\n")


# 主函数
def main():
    # 获取文件夹内音频文件
    wav_files = get_audio_files(folder1, '.wav')
    mp3_files = get_audio_files(folder2, '.mp3')

    # 处理第一组音频，提取第二段环境音
    process_first_group_files(wav_files, output_folder1_silence)

    # 处理第二组音频，提取第一段环境音
    process_second_group_files(mp3_files, output_folder2_silence)


if __name__ == "__main__":
    main()
