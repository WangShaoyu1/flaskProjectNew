# -*- coding: utf-8 -*-
import requests
import time
import hashlib
import base64
from utils.iflytek import APPID, API_KEY, ImageName, ImageUrl, FilePath, getHeader, getBody

# 人脸特征分析颜值webapi接口地址
URL = "http://tupapi.xfyun.cn/v1/face_score"

# Record the time before sending the request
start_time = time.time()

r_face_score = requests.post(URL, data=getBody(FilePath), headers=getHeader(ImageName, ImageUrl)).text
# Record the time after receiving the response
end_time = time.time()

duratation_face_score = round(end_time - start_time, 3)
