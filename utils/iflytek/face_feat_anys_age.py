# -*- coding: utf-8 -*-
import json

import requests
import time
import asyncio
import aiohttp
from aiohttp import ClientError, ClientResponseError
from utils.iflytek import APPID, API_KEY, ImageName, ImageUrl, FilePath, getHeader, getBody

URL = "http://tupapi.xfyun.cn/v1/age"
label_dict = {
    "0": {range: [0, 1], "desc": "0-1岁"},
    "1": {range: [2, 5], "desc": "2-5岁"},
    "2": {range: [6, 10], "desc": "6-10岁"},
    "3": {range: [11, 15], "desc": "11-15岁"},
    "4": {range: [16, 20], "desc": "16-20岁"},
    "5": {range: [21, 25], "desc": "21-25岁"},
    "12": {range: [26, 30], "desc": "26-30岁"},
    "6": {range: [31, 40], "desc": "31-40岁"},
    "7": {range: [41, 50], "desc": "41-50岁"},
    "8": {range: [51, 60], "desc": "51-60岁"},
    "9": {range: [61, 80], "desc": "61-80岁"},
    "10": {range: [80, 120], "desc": "80岁以上"},
    "11": {range: [], "desc": "其他"},
}


async def fetch_age(session, image_name, file_path, retries=1, delay=2):
    start_time = time.time()
    for attempt in range(retries):
        try:
            async with session.post(URL, data=getBody(file_path), headers=getHeader(image_name, ImageUrl)) as response:
                response.raise_for_status()
                text_data = await response.text()
                data = json.loads(text_data)
                # 根据返回内容中的 'code' 字段进行不同的操作
                if data["code"] == 0:
                    r_data = data["data"]
                    label = (r_data["fileList"] or [])[0]["label"]
                    r_age = {"desc": label_dict[str(label)]["desc"], "label": label}
                    print(f"age: {r_data}")
                    return r_age, round(time.time() - start_time, 2)
                else:
                    print(f"API Error: {data['desc']}")
        except (ClientResponseError, ClientError, Exception) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)

    return None, round(time.time() - start_time, 2)


def fetch_age_requests():
    # Record the time before sending the request
    start_time = time.time()
    r_age = {}
    r_response = requests.post(URL, data=getBody(FilePath), headers=getHeader(ImageName, ImageUrl))

    # 检查 HTTP 响应状态码
    if r_response.status_code == 200:
        try:
            data = r_response.json()
            # 根据返回内容中的 'code' 字段进行不同的操作
            if data["code"] == 0:
                # 获取返回内容中的 'data' 字段
                r_data = r_response.json()["data"]
                label = (r_data["fileList"] or [])[0]["label"]
                r_age = {"desc": label_dict[str(label)]["descriptions"], "label": label}
                print(f"r_age: {r_data}")
        except NameError:
            print("Error response code: %d" % r_response.status_code)
    else:
        print("Error response code: %d" % r_response.status_code)

    # r = requests.post(URL, headers=getHeader(ImageName, ImageUrl))

    # Record the time after receiving the response
    end_time = time.time()

    duratation = round(end_time - start_time, 3)
    print(f"r_age: {r_age}")
    return r_age, duratation


# 添加主函数部分
if __name__ == "__main__":
    async def main():
        async with aiohttp.ClientSession() as session:
            r_age, duration = await fetch_age(session)
            print(f"Result: {r_age}, Duration: {duration}秒")


    asyncio.run(main())
