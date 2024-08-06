from PIL import Image
import os


def compress_image(image_path, output_path, max_size_kb):
    # ��ͼ��
    img = Image.open(image_path)
    quality = 95

    # ѹ��ͼ��ֱ�������С����
    while True:
        # ����ͼ��ָ����·��
        img.save(output_path, "JPEG", quality=quality)
        file_size_kb = os.path.getsize(output_path) / 1024  # �ֽ�ת��ΪKB

        if file_size_kb <= max_size_kb or quality <= 10:
            break

        quality -= 5

    print(f"Compressed image saved to {output_path} with size {file_size_kb:.2f} KB")


# ʾ��ʹ��
# compress_image("../../app/static/img/test/test2-boy-o.jpg", "../../app/static/img/crop/test2-boy-o-crop.jpg")