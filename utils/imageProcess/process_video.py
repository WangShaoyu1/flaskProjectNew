import os
import cv2
import time
import imageio
import ffmpeg
import concurrent.futures
import numpy as np
import torch

video_path = "D:\\驱动精灵搬家目录\\视频文件\\介绍商品.mp4"
img_save_path = "./images"
os.makedirs(img_save_path, exist_ok=True)


def get_video_fps(path):
    video = cv2.VideoCapture(path)
    fps = video.get(cv2.CAP_PROP_FPS)
    video.release()
    return fps


#  通过 imageio 提取视频帧
def process_img_by_imageio(path):
    start_time = time.time()
    reader = imageio.get_reader(path)
    for i, im in enumerate(reader):
        imageio.imwrite(f"{img_save_path}/{str(i).zfill(8)}.png", im)
    print(f"Extracted {i + 1} frames in {time.time() - start_time:.2f} seconds")
    print(f"Video FPS: {get_video_fps(path)}")


# 通过 cv2 提取视频帧
def process_img_by_cv2(path):
    start_time = time.time()
    # 使用 OpenCV 读取视频
    cap = cv2.VideoCapture(path)
    frame_index = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # 使用 OpenCV 保存帧
        cv2.imwrite(f"{img_save_path}/{str(frame_index).zfill(8)}.png", frame)
        frame_index += 1
        print(f"Extracted frame {frame_index}")

    cap.release()
    print(f"Extracted  frames in {time.time() - start_time:.2f} seconds")
    print(f"Video FPS: {get_video_fps(path)}")


# 通过 cv2多线程 提取视频帧
def process_img_by_cv2_multithread(path):
    start_time = time.time()
    # 使用 OpenCV 读取视频
    cap = cv2.VideoCapture(path)
    frame_index = 0

    def save_frame(frames, index):
        cv2.imwrite(f"{img_save_path}/{str(index).zfill(8)}.png", frames)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            executor.submit(save_frame, frame, frame_index)
            frame_index += 1

    cap.release()
    print(f"Extracted  frames in {time.time() - start_time:.2f} seconds")
    print(f"Video FPS: {get_video_fps(path)}")


def process_img_by_cv2_batch(path):
    start_time = time.time()
    cap = cv2.VideoCapture(path)
    frame_index = 0
    batch_size = 5
    frames = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

        # 当达到批处理大小时，进行处理
        if len(frames) >= batch_size:
            # 批量保存
            for i in range(len(frames)):
                cv2.imwrite(f"{img_save_path}/{str(frame_index).zfill(8)}.png", frames[i])
                frame_index += 1
            frames = []  # 清空帧列表

    # 处理剩余的帧
    for i in range(len(frames)):
        cv2.imwrite(f"{img_save_path}/{str(frame_index).zfill(8)}.png", frames[i])

    cap.release()

    print(f"Extracted  frames in {time.time() - start_time:.2f} seconds")
    print(f"Video FPS: {get_video_fps(path)}")


def process_img_by_GPU(path):
    start_time = time.time()
    cap = cv2.VideoCapture(video_path)
    frame_index = 0
    # 使用 PyTorch Tensor 存储图像帧
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 将帧转为 Tensor，并移动到 GPU
        frame_tensor = torch.from_numpy(frame).permute(2, 0, 1).float().to(device)  # 转为 C x H x W

        # 在 GPU 上进行处理（例如，归一化）
        frame_tensor = frame_tensor / 255.0

        # 如果需要可以进行更多处理

        # 将处理后的帧转回 CPU 并保存
        output_frame = (frame_tensor.permute(1, 2, 0) * 255).byte().cpu().numpy()
        cv2.imwrite(f"{img_save_path}/{str(frame_index).zfill(8)}.png", output_frame)
        frame_index += 1

    cap.release()
    print(f"Extracted frames in {time.time() - start_time:.2f} seconds")
    print(f"Video FPS: {get_video_fps(path)}")


process_img_by_cv2_multithread(video_path)