# -*- coding: utf-8 -*-
import requests
import time
from utils.iflytek import APPID, API_KEY, ImageName, ImageUrl, FilePath, getHeader, getBody

# 人脸特征分析性别webapi接口地址
URL = "https://tupapi.xfyun.cn/v1/sex"
label_sex_dict = {
    "0": {"descriptions": "男人"},
    "1": {"descriptions": "女人"},
    "2": {"descriptions": "难以辨认"},
    "3": {"descriptions": "多人"},
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
            label_sex = (r_data["fileList"] or [])[0]["label"]
            r_sex = {"desc": label_sex_dict[str(label_sex)]["descriptions"], "label_sex": label_sex}
            print(f"sex: {r_data}")
    except NameError:
        print("Error response code: %d" % r_response.status_code)
else:
    print("Error response code: %d" % r_response.status_code)

# Record the time after receiving the response
end_time = time.time()

duratation_sex = round(end_time - start_time, 3)
print(f"r_sex: {r_sex}")
