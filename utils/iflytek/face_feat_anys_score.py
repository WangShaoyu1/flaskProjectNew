# -*- coding: utf-8 -*-
import requests
import time
import hashlib
import base64
from utils.iflytek import APPID, API_KEY, ImageName, ImageUrl, FilePath, getHeader, getBody

# 人脸特征分析颜值webapi接口地址
URL = "https://tupapi.xfyun.cn/v1/face_score"
label_face_score_dict = {
    "0": {"descriptions": "漂亮"},
    "1": {"descriptions": "好看"},
    "2": {"descriptions": "普通"},
    "3": {"descriptions": "难看"},
    "4": {"descriptions": "其他"},
    "5": {"descriptions": "半人脸"},
    "6": {"descriptions": "多人"},
}

# Record the time before sending the request
start_time = time.time()

r_response = requests.post(URL, data=getBody(FilePath), headers=getHeader(ImageName, ImageUrl))

# 检查 HTTP 响应状态码
if r_response.status_code == 200:
    try:
        data = r_response.json()
        # 根据返回内容中的 'code' 字段进行不同的操作
        if data["code"] == 0:
            # 获取返回内容中的 'data' 字段
            r_data = r_response.json()["data"]
            label_face_score = (r_data["fileList"] or [])[0]["label"]
            r_face_score = {"desc": label_face_score_dict[str(label_face_score)]["descriptions"],
                            "label_face_score": label_face_score}
            print(f"face_score: {r_data}")
    except NameError:
        print("Error response code: %d" % r_response.status_code)
else:
    print("Error response code: %d" % r_response.status_code)

# Record the time after receiving the response
end_time = time.time()

duratation_face_score = round(end_time - start_time, 3)
print(f"face_score:{r_face_score}")
