import cv2
from PIL import Image


def crop_face(image_path, output_path):
    # 读取图像
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 使用 OpenCV 的预训练人脸检测器
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        print("No face detected.")
        return

    # 选择第一个检测到的人脸
    x, y, w, h = faces[0]

    # 计算要裁剪的范围
    center_x, center_y = x + w // 2, y + h // 2
    crop_width = 900
    crop_height = 900
    crop_x1 = max(center_x - crop_width // 2, 0)
    crop_y1 = max(center_y - crop_height // 2, 0)
    crop_x2 = min(center_x + crop_width // 2, image.shape[1])
    crop_y2 = min(center_y + crop_height // 2, image.shape[0])

    cropped_image = image[crop_y1:crop_y2, crop_x1:crop_x2]

    # 保存裁剪后的图像
    cv2.imwrite(output_path, cropped_image)
    print(f"Cropped image saved to {output_path}")


# 示例使用
# crop_face("../../app/static/img/test/test2-boy-o.jpg", "../../app/static/img/crop/test2-boy-o-crop.jpg")
