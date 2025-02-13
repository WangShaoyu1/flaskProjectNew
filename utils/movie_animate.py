import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from moviepy.editor import ImageSequenceClip

# 假设这是每日票房数据
dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
ticket_sales = np.random.randint(100000, 1000000, size=len(dates))

# 生成图表
images = []
for i in range(len(dates)):
    plt.figure(figsize=(10, 6))
    plt.plot(dates[:i+1], ticket_sales[:i+1], marker='o', color='b', label='哪吒2票房')
    plt.xlabel('日期')
    plt.ylabel('票房(元)')
    plt.title('哪吒2每日票房进展')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # 保存每一帧图像
    img_path = f"frame_{i}.png"
    plt.savefig(img_path)
    images.append(img_path)
    plt.close()

# 使用moviepy将图像序列合成视频
clip = ImageSequenceClip(images, fps=30)
clip.write_videofile("ticket_sales_progress.mp4", codec='libx264')

