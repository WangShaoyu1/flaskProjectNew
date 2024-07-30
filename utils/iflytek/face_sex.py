# -*- coding: utf-8 -*-
import requests
import time
from utils.iflytek import APPID, API_KEY, ImageName, ImageUrl, FilePath, getHeader, getBody

# 人脸特征分析性别webapi接口地址
URL = "http://tupapi.xfyun.cn/v1/sex"

# Record the time before sending the request
start_time = time.time()

r_sex = requests.post(URL, data=getBody(FilePath), headers=getHeader(ImageName, ImageUrl)).text
# r = requests.post(URL, headers=getHeader(ImageName, ImageUrl))

# Record the time after receiving the response
end_time = time.time()

duratation_sex = round(end_time - start_time, 3)
