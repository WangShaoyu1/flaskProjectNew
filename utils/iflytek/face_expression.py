# -*- coding: utf-8 -*-
import requests
import time
import hashlib
import base64
from utils.iflytek import APPID, API_KEY, ImageName, ImageUrl, FilePath, getHeader, getBody

# 人脸特征分析表情webapi接口地址
URL = "http://tupapi.xfyun.cn/v1/expression"

# Record the time before sending the request
start_time = time.time()

r_expression = requests.post(URL, data=getBody(FilePath), headers=getHeader(ImageName, ImageUrl)).text
# r = requests.post(URL, headers=getHeader(ImageName, ImageUrl))

# Record the time after receiving the response
end_time = time.time()

duratation_expression = round(end_time - start_time, 3)
