import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip

# 指定图片和视频的保存目录
img_dir = r"D:\gitlab\flaskProjectNew\utils\movie_animate\media"
video_dir = r"D:\gitlab\flaskProjectNew\utils\movie_animate\media"

# 如果目录不存在则创建
os.makedirs(img_dir, exist_ok=True)
os.makedirs(video_dir, exist_ok=True)

# 设置视频总时长（秒）
video_duration = 15

# 生成10天的票房数据作为示例
num_frames = 10
dates = pd.date_range('2024-01-01', periods=num_frames, freq='D')
ticket_sales = np.random.randint(100000, 1000000, size=num_frames)

# 存储生成的每一帧图片的完整路径
image_paths = []
for i in range(num_frames):
    plt.figure(figsize=(10, 6))
    plt.plot(dates[:i + 1], ticket_sales[:i + 1], marker='o', color='b', label='哪吒2票房')
    plt.xlabel('日期')
    plt.ylabel('票房(元)')
    plt.title('哪吒2每日票房进展')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    # 构造当前帧图片的完整保存路径
    frame_filename = f"frame_{i}.png"
    frame_filepath = os.path.join(img_dir, frame_filename)
    plt.savefig(frame_filepath)
    image_paths.append(frame_filepath)
    plt.close()

# 根据帧数计算 fps，使视频总时长为 5 秒
fps = num_frames / video_duration

# 使用 ImageSequenceClip 将图片序列合成视频
clip = ImageSequenceClip(image_paths, fps=fps)
output_video = os.path.join(video_dir, "ticket_sales_progress.mp4")
clip.write_videofile(output_video, codec='libx264')
