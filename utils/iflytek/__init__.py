import time
import hashlib
import base64

# 应用ID  (必须为webapi类型应用，并人脸特征分析服务，参考帖子如何创建一个webapi应用：http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=36481)
# APPID = "a327ed87"
APPID = "0703d0ec"
# 接口密钥(webapi类型应用开通人脸特征分析服务后，控制台--我的应用---人脸特征分析---服务的apikey)
# API_KEY = "4bd46c063d171c6d6ed23d7bbdcce8a4"
API_KEY = "6091cc62afeb1daa392e69fbda93e123"
ImageName = "test2-boy-o.jpg"
ImageUrl = "http://hbimg.b0.upaiyun.com/a09289289df694cd6157f997ffa017cc44d4ca9e288fb-OehMYA_fw658"
# 图片数据可以通过两种方式上传，第一种在请求头设置image_url参数，第二种将图片二进制数据写入请求体中。若同时设置，以第一种为准。
# 此demo使用第一种方式进行上传图片地址，如果想使用第二种方式，将图片二进制数据写入请求体即可。
FilePath = r"D:\gitlab\flaskProjectNew\app\static\img\test3-boy.jpg"


def getHeader(image_name, image_url=None):
    curTime = str(int(time.time()))
    # param = "{\"image_name\":\"" + image_name + "\",\"image_url\":\"" + image_url + "\"}"
    param = "{\"image_name\":\"" + image_name + "\"}"
    parambase64 = base64.b64encode(param.encode('utf-8'))
    tmp = str(parambase64, 'utf-8')

    m2 = hashlib.md5()
    m2.update((API_KEY + curTime + tmp).encode('utf-8'))
    checksum = m2.hexdigest()

    header = {
        'X-CurTime': curTime,
        'X-Param': parambase64,
        'X-Appid': APPID,
        'X-CheckSum': checksum,
    }
    return header


def getBody(filepath):
    binfile = open(filepath, 'rb')
    data = binfile.read()
    return data
