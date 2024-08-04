# -*- coding: utf-8 -*-
import json
import requests
import time
import asyncio
import aiohttp
from aiohttp import ClientError, ClientResponseError
from utils.iflytek import APPID, API_KEY, ImageName, ImageUrl, FilePath, getHeader, getBody

# 人脸特征分析性别webapi接口地址
URL = "http://tupapi.xfyun.cn/v1/sex"
label_gender_dict = {
    "0": {"desc": "男人"},
    "1": {"desc": "女人"},
    "2": {"desc": "难以辨认"},
    "3": {"desc": "多人"},
}


async def fetch_gender(session, image_name, file_path, retries=1, delay=2):
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
                    r_gender = {"desc": label_gender_dict[str(label)]["desc"], "label": label}
                    print(f"r_gender: {r_data}")
                    return r_gender, round(time.time() - start_time, 2)
                else:
                    print(f"API Error: {data['desc']}")
        except (ClientResponseError, ClientError, Exception) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)

    return None, round(time.time() - start_time, 2)


def fetch_gender_requests():
    # Record the time before sending the request
    start_time = time.time()
    r_gender = {}
    r_response = requests.post(URL, data=getBody(FilePath), headers=getHeader(ImageName, ImageUrl))

    # 检查 HTTP 响应状态码
    if r_response.status_code == 200:
        try:
            data = r_response.json()
            # 根据返回内容中的 'code' 字段进行不同的操作
            if data["code"] == 0:
                # 获取返回内容中的 'data' 字段
                r_data = r_response.json()["data"]
                label_gender = (r_data["fileList"] or [])[0]["label"]
                r_gender = {"desc": label_gender_dict[str(label_gender)]["desc"], "label_gender": label_gender}
                print(f"gender: {r_data}")
        except NameError:
            print("Error response code: %d" % r_response.status_code)
    else:
        print("Error response code: %d" % r_response.status_code)

    # Record the time after receiving the response
    end_time = time.time()

    duratation = round(end_time - start_time, 2)
    print(f"r_gender: {r_gender}")
    return r_gender, duratation


# 添加主函数部分
if __name__ == "__main__":
    async def main():
        async with aiohttp.ClientSession() as session:
            r_gender, duration = await fetch_gender(session)
            print(f"Result: {r_gender}, Duration: {duration}秒")


    asyncio.run(main())
