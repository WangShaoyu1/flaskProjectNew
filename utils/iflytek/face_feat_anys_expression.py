# -*- coding: utf-8 -*-
import requests
import time
import hashlib
import base64
from utils.iflytek import APPID, API_KEY, ImageName, ImageUrl, FilePath, getHeader, getBody

# 人脸特征分析表情webapi接口地址
URL = "https://tupapi.xfyun.cn/v1/expression"
label_expression_dict = {
    "0": {"descriptions": "其他(非人脸表情图片)"},
    "1": {"descriptions": "其他表情"},
    "2": {"descriptions": "喜悦"},
    "3": {"descriptions": "愤怒"},
    "4": {"descriptions": "悲伤"},
    "5": {"descriptions": "惊恐"},
    "6": {"descriptions": "厌恶"},
    "7": {"descriptions": "中性"},
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
            label_expression = (r_data["fileList"] or [])[0]["label"]
            r_expression = {"desc": label_expression_dict[str(label_expression)]["descriptions"],
                            "label_expression": label_expression}
            print(f"expression: {r_data}")
    except NameError:
        print("Error response code: %d" % r_response.status_code)
else:
    print("Error response code: %d" % r_response.status_code)

# r = requests.post(URL, headers=getHeader(ImageName, ImageUrl))

# Record the time after receiving the response
end_time = time.time()

duratation_expression = round(end_time - start_time, 3)
print(f"r_expression: {r_expression}")