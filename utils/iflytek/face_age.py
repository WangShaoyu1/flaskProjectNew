# -*- coding: utf-8 -*-
import json

import requests
import time
import hashlib
import base64
from utils.iflytek import APPID, API_KEY, ImageName, ImageUrl, FilePath, getHeader, getBody

URL = "http://tupapi.xfyun.cn/v1/age"
label_age_dict = {
    "0": {range: [0, 1], "descriptions": "0-1岁"},
    "1": {range: [2, 5], "descriptions": "2-5岁"},
    "2": {range: [6, 10], "descriptions": "6-10岁"},
    "3": {range: [11, 15], "descriptions": "11-15岁"},
    "4": {range: [16, 20], "descriptions": "16-20岁"},
    "5": {range: [21, 25], "descriptions": "21-25岁"},
    "12": {range: [26, 30], "descriptions": "26-30岁"},
    "6": {range: [31, 40], "descriptions": "31-40岁"},
    "7": {range: [41, 50], "descriptions": "41-50岁"},
    "8": {range: [51, 60], "descriptions": "51-60岁"},
    "9": {range: [61, 80], "descriptions": "61-80岁"},
    "10": {range: [80, 120], "descriptions": "80岁以上"},
    "11": {range: [], "descriptions": "其他"},
}
# Record the time before sending the request
start_time = time.time()

r_response = requests.post(URL, data=getBody(FilePath), headers=getHeader(ImageName, ImageUrl)).json()
label_age = r_response["data"]["fileList"][0]["label"]
r_age = label_age_dict.get(str(label_age))["descriptions"]

# r = requests.post(URL, headers=getHeader(ImageName, ImageUrl))

# Record the time after receiving the response
end_time = time.time()

duratation_age = round(end_time - start_time, 3)
print(r_age)
