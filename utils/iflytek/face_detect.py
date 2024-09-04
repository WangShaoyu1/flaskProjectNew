#
# 人脸检测和属性分析 WebAPI 接口调用示例
# 运行前：请先填写Appid、APIKey、APISecret以及图片路径
# 运行方法：直接运行 main 即可
# 结果： 控制台输出结果信息
#
# 接口文档（必看）：https://www.xfyun.cn/doc/face/xf-face-detect/API.html
#

from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
import time
from urllib.parse import urlencode
import os
import traceback
import json
import requests
from utils.iflytek import APPID, ImageName, ImageUrl, FilePath, getHeader, getBody
from utils import util

URL = "https://api.xf-yun.com/v1/private/"
API_KEY = "e419795a1e6fb57f49a3cdedf14e2bdc"
API_Secret = "YWNhNDljYzFkNjRjODc0YTE3ODRhMDM5"
SERVER_ID = "s67c9c78c"
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp')
FilePath = r"D:\gitlab\flaskProjectNew\utils\iflytek\img\crop"

hair_dict = {
    "0": {"desc": "光头"},
    "1": {"desc": "短发"},
    "2": {"desc": "长发"},
}
glass_dict = {
    "0": {"desc": "不戴眼镜"},
    "1": {"desc": "戴眼镜"},
}
gender_dict = {
    "0": {"desc": "男"},
    "1": {"desc": "女"},
}
expression_dict = {
    "0": {"desc": "惊讶"},
    "1": {"desc": "害怕"},
    "2": {"desc": "厌恶"},
    "3": {"desc": "高兴"},
    "4": {"desc": "悲伤"},
    "5": {"desc": "生气"},
    "6": {"desc": "正常"},
}

beard_dict = {
    "0": {"desc": "没有胡子"},
    "1": {"desc": "有胡子"},
}
mask_dict = {
    "0": {"desc": "没戴口罩"},
    "1": {"desc": "戴口罩"},
}


class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(this, host, path, schema):
        this.host = host
        this.path = path
        this.schema = schema
        pass


# 进行sha256加密和base64编码
def sha256base64(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
    return digest


def parse_url(requset_url):
    stidx = requset_url.index("://")
    host = requset_url[stidx + 3:]
    schema = requset_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + requset_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url(host, path, schema)
    return u


def assemble_ws_auth_url(requset_url, method="GET", api_key="", api_secret=""):
    u = parse_url(requset_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))

    # date = "Thu, 12 Dec 2019 01:57:27 GMT"
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)

    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }

    return requset_url + "?" + urlencode(values)


def gen_body(appid, img_path, server_id):
    with open(img_path, 'rb') as f:
        img_data = f.read()
    body = {
        "header": {
            "app_id": appid,
            "status": 3
        },
        "parameter": {
            server_id: {
                "service_kind": "face_detect",
                "detect_points": "1",  # 检测特征点
                "detect_property": "1",  # 检测人脸属性
                "face_detect_result": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
            }
        },
        "payload": {
            "input1": {
                "encoding": "jpg",
                "status": 3,
                "image": str(base64.b64encode(img_data), 'utf-8')
            }
        }
    }
    return json.dumps(body)


def run(appid, apikey, apisecret, img_path, server_id='s67c9c78c', file=''):
    url = f'{URL}{server_id}'.format(server_id)
    request_url = assemble_ws_auth_url(url, "POST", apikey, apisecret)
    headers = {'content-type': "application/json", 'host': 'api.xf-yun.com', 'app_id': appid}

    response = requests.post(request_url, data=gen_body(appid, img_path, server_id), headers=headers)
    # resp_data = json.loads(response.content.decode('utf-8'))
    resp_data = response.json()
    resp_data_text = base64.b64decode(resp_data['payload']['face_detect_result']['text']).decode()
    print(f"resp_data_text: {resp_data_text}")
    final_data = handle_data(json.loads(resp_data_text))[0]
    final_string = handle_data(json.loads(resp_data_text))[1]
    print(f"final_data: {final_data}")
    util.write_to_file('temp_data_dir/iflytek.log', f'\n--------------------face_detect--------------------\n')
    # util.write_to_file('temp_data_dir/iflytek.log', f"{final_data}", need_json=True)
    util.write_to_file('temp_data_dir/iflytek.log', f"\n{file}--{final_string}")


def handle_data(data):
    temp = {}
    if data["ret"] == 0:
        for i in range(data["face_num"]):
            temp[f"{i}"] = {
                "gender": {
                    "desc": gender_dict[str(data[f"face_{i + 1}"]["property"]["gender"])]["desc"],
                    "value": data[f"face_{i + 1}"]["property"]["gender"]
                },
                "glass": {
                    "desc": glass_dict[str(data[f"face_{i + 1}"]["property"]["glass"])]["desc"],
                    "value": data[f"face_{i + 1}"]["property"]["glass"]
                },
                "hair": {
                    "desc": hair_dict[str(data[f"face_{i + 1}"]["property"]["hair"])]["desc"],
                    "value": data[f"face_{i + 1}"]["property"]["hair"]
                },
                "expression": {
                    "desc": expression_dict[str(data[f"face_{i + 1}"]["property"]["expression"])]["desc"],
                    "value": data[f"face_{i + 1}"]["property"]["expression"]
                },
                "beard": {
                    "desc": beard_dict[str(data[f"face_{i + 1}"]["property"]["beard"])]["desc"],
                    "value": data[f"face_{i + 1}"]["property"]["beard"]
                },
                "mask": {
                    "desc": mask_dict[str(data[f"face_{i + 1}"]["property"]["mask"])]["desc"],
                    "value": data[f"face_{i + 1}"]["property"]["mask"]
                },
            }
        string = f"这是一名{temp['0']['gender']['desc']}性，{temp['0']['glass']['desc']}，{temp['0']['hair']['desc']}，表情{temp['0']['expression']['desc']}，{temp['0']['beard']['desc']}，{temp['0']['mask']['desc']}。"
        return temp, string
    else:
        return temp, "未检测到人脸"


# Function to process all images in a folder
def process_images_in_folder(folder_path, appid, apikey, apisecret, server_id):
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(IMAGE_EXTENSIONS):
                img_path = os.path.join(root, file)
                run(appid, apikey, apisecret, img_path, server_id, file)
                print(f"Processed {file}. Waiting 2 seconds before next request...")
                time.sleep(2)  # 延时5秒


# 请填写控制台获取的APPID、APISecret、APIKey以及要检测的图片路径
if __name__ == '__main__':
    # Record the time before sending the request
    start_time = time.time()
    process_images_in_folder(FilePath, APPID, API_KEY, API_Secret, SERVER_ID)
    # Record the time after receiving the response
    end_time = time.time()

    util.write_to_file('temp_data_dir/iflytek.log',
                       f'\n--------------------face_detect耗时：{round(end_time - start_time, 3)}秒--------------------\n')
