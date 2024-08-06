from PIL import Image
import os


def compress_image(image_path, output_path, max_size_kb):
    # 打开图像
    img = Image.open(image_path)
    quality = 95

    # 压缩图像直到满足大小限制
    while True:
        # 保存图像到指定的路径
        img.save(output_path, "JPEG", quality=quality)
        file_size_kb = os.path.getsize(output_path) / 1024  # 字节转换为KB

        if file_size_kb <= max_size_kb or quality <= 10:
            break

        quality -= 5

    print(f"Compressed image saved to {output_path} with size {file_size_kb:.2f} KB")


# 示例使用
# compress_image("../../app/static/img/test/test2-boy-o.jpg", "../../app/static/img/crop/test2-boy-o-crop.jpg")