import os
import random
import subprocess
import threading
import time
import shutil

# 配置空白音频的时长（单位：秒）
silence_duration = 0.3  # 你可以根据需要更改这个值
select_random_files_num = 3000  # 随机选择的音频文件数量
# 设置文件夹路径
folder1 = r"D:\语音测试1127\cutted\小万小万-测试集"  # wav 文件夹
folder2 = r"D:\语音测试1127\cutted\识别率测试音频"  # mp3 文件夹
output_folder = fr"D:\语音测试1127\ffmpeg\output_latest_{silence_duration}"  # 所有组合音频输出路径
final_output_folder = fr"D:\语音测试1127\ffmpeg\random_{silence_duration}_{select_random_files_num}"  # 随机选择后的音频保存路径
output_folder_test = fr"D:\语音测试1127\ffmpeg\output_test_{silence_duration}"
final_output_folder_test = fr"D:\语音测试1127\ffmpeg\random_test_{silence_duration}"
need_test = False  # 是否需要测试


# 生成文件名
def generate_filename(file1, file2):
    filename1 = os.path.splitext(file1)[0][:11]  # 取文件名的前1 1位
    filename2 = os.path.splitext(file2)[0]
    return f"{filename1}_{filename2}.mp3"


# 使用ffmpeg拼接音频文件，并插入空白音频
def concat_audio_with_silence(file1, file2, output_file, silence_duration_sec):
    # 生成空白音频
    silence_file = "silence.wav"
    subprocess.run([
        'ffmpeg', '-y', '-f', 'lavfi', '-t', str(silence_duration_sec),
        '-i', 'anullsrc=r=44100:cl=stereo', silence_file
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 拼接音频（包括空白音频）
    cmd = [
        'ffmpeg', '-y',
        '-i', file1,
        '-i', silence_file,
        '-i', file2,
        '-filter_complex', '[0][1][2]concat=n=3:v=0:a=1[out]',
        '-map', '[out]',
        output_file
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 删除临时的空白音频文件


# 获取文件夹内所有音频文件
def get_audio_files(folder, ext):
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(ext)]


# 生成空白音频文件，固定时长（比如 5 秒）
def generate_static_silence(silence_file):
    if not os.path.exists(silence_file):  # 如果文件不存在才生成
        print(f"生成空白音频文件：{silence_file}，时长：{silence_duration}秒")
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-t', str(silence_duration),
            '-i', 'anullsrc=r=44100:cl=stereo', silence_file
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        print(f"静态空白音频文件已经存在：{silence_file}")


# 处理音频文件（合并）
def process_audio_files(folder1_files, folder2_files, output_folder_inner):
    if not os.path.exists(output_folder_inner):
        os.makedirs(output_folder_inner)

    threads = []
    start_time = time.time()  # 记录开始时间
    total_files = len(folder1_files) * len(folder2_files)  # 计算总共要生成的文件数
    count = 0  # 用于计数已生成的音频数量

    for file1 in folder1_files:
        for file2 in folder2_files:
            output_file = os.path.join(output_folder_inner,
                                       generate_filename(os.path.basename(file1), os.path.basename(file2)))
            thread = threading.Thread(target=concat_audio_with_silence,
                                      args=(file1, file2, output_file, silence_duration))
            threads.append(thread)
            thread.start()

            count += 1
            # 每生成50个文件，打印日志
            if count % 100 == 0:
                print(f"已生成 {count} 个音频文件，正在合并音频文件: {file1} 和 {file2} 到 {output_file}...")

            # 进程过多时，等待某些线程完成
            if len(threads) >= 24:  # 控制最大线程数
                for t in threads:
                    t.join()
                threads = []

    # 等待剩余线程
    for t in threads:
        t.join()

    end_time = time.time()  # 记录结束时间
    total_duration = end_time - start_time
    print(f"生成 {total_files} 个音频文件，总共花费时间: {total_duration:.2f}秒")


# 随机选择音频文件并保存
def select_random_files(output_folder_inner, final_output_folder_inner, num_files):
    # 如果 final_output_folder_inner 中已有文件，则清空该文件夹
    if os.path.exists(final_output_folder_inner):
        for file in os.listdir(final_output_folder_inner):
            file_path = os.path.join(final_output_folder_inner, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
            else:
                # 如果是目录，递归删除目录中的文件
                os.rmdir(file_path)
    if not os.path.exists(final_output_folder_inner):
        os.makedirs(final_output_folder_inner)

    output_files = [os.path.join(output_folder_inner, f) for f in os.listdir(output_folder_inner)]
    print(f"共有 {len(output_files)} 个音频文件")
    selected_files = random.sample(output_files, num_files)

    for file in selected_files:
        dest_file = os.path.join(final_output_folder_inner, os.path.basename(file))
        # os.rename(file, dest_file) # 移动文件，变相删除文件
        shutil.copy2(file, dest_file)

    print(f"随机选择了 {num_files} 个音频文件并保存到 {final_output_folder_inner}")


def mkdirs_files():
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if not os.path.exists(output_folder_test):
        os.makedirs(output_folder_test)

    if not os.path.exists(final_output_folder):
        os.makedirs(final_output_folder)

    if not os.path.exists(final_output_folder_test):
        os.makedirs(final_output_folder_test)


# 主函数
def main():
    # 确保 output_folder 和 final_output_folder 存在
    mkdirs_files();
    silence_file = 'silence.wav'  # 静态空白音频文件路径
    # 生成静态空白音频文件
    generate_static_silence(silence_file)

    # 获取文件夹内音频文件
    wav_files = get_audio_files(folder1, '.wav')
    mp3_files = get_audio_files(folder2, '.mp3')

    # 如果需要测试数据，就直接生成
    if need_test:
        process_audio_files(wav_files[:4], mp3_files[:4], output_folder_test)
        select_random_files(output_folder_test, final_output_folder_test, 6)
    else:
        # 如果 output_folder 中已有文件，则跳过合并过程
        if not os.listdir(output_folder):
            print("开始处理音频文件合并...")
            # 处理音频文件，合并
            process_audio_files(wav_files, mp3_files, output_folder)
        else:
            print(f"{output_folder} 中已经有音频文件，跳过合并过程。")

        # 随机选择音频文件（例如选择100个）
        select_random_files(output_folder, final_output_folder, select_random_files_num)


if __name__ == "__main__":
    main()
