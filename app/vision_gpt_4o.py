import base64
import requests
import os
import time
from app.config import Config
from utils import util


def encode_image(image_path):
    """Encode an image file to a Base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def create_payload(base64_image):
    """Create the payload for the API request."""
    return {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "你现在作为一个图片识别小能手，从照片中提取关键信息，并按照给定的格式输出，额外要求一定要输出年龄评估值,可以是一个年龄范围或者年龄准确值。这是一名{男|女}性，年龄{}岁，颜值{漂亮|好看|普通|难看}，{没}戴眼镜，{短发|长发|光头}，表情{正常|开心|悲伤}，{有|没有}胡子，{没|没有}戴口罩"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }


def process_image(image_path):
    """Process an individual image and make an API request."""
    start_time = time.time()
    base64_image = encode_image(image_path)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {Config.OPENAI_API_KEY}"
    }
    payload = create_payload(base64_image)
    response = requests.post(f"{Config.OPENAI_BASE_URL}/chat/completions", headers=headers, json=payload)
    content = response.json()
    end_time = time.time()
    util.write_to_file('temp_data_dir/vision.log', f"{os.path.basename(image_path)}")
    util.write_to_file('temp_data_dir/vision.log', f"---{content['choices'][0]['message']['content']}")
    util.write_to_file('temp_data_dir/vision.log', f"---耗时{round(end_time - start_time, 2)}秒\n")


def process_image_folder(folder_path):
    start_total_time = time.time()
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    for image_file in image_files:
        image_path = os.path.join(folder_path, image_file)
        process_image(image_path)
        time.sleep(5)
    end_total_time = time.time()
    util.write_to_file('temp_data_dir/vision.log',
                       f"共处理图片{len(image_files)}张，共耗时:{round(end_total_time - start_total_time, 2)}秒\n")


if __name__ == "__main__":
    # Path to your image folder
    image_folder_path = fr"D:\gitlab\flaskProjectNew\utils\iflytek\img\crop"
    process_image_folder(image_folder_path)
