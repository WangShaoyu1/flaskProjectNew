import time
import hashlib
import base64

# Ӧ��ID  (����Ϊwebapi����Ӧ�ã������������������񣬲ο�������δ���һ��webapiӦ�ã�http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=36481)
# APPID = "a327ed87"
APPID = "0703d0ec"
# �ӿ���Կ(webapi����Ӧ�ÿ�ͨ����������������󣬿���̨--�ҵ�Ӧ��---������������---�����apikey)
# API_KEY = "4bd46c063d171c6d6ed23d7bbdcce8a4"
API_KEY = "6091cc62afeb1daa392e69fbda93e123"
ImageName = "test2-boy-o.jpg"
ImageUrl = "http://hbimg.b0.upaiyun.com/a09289289df694cd6157f997ffa017cc44d4ca9e288fb-OehMYA_fw658"
# ͼƬ���ݿ���ͨ�����ַ�ʽ�ϴ�����һ��������ͷ����image_url�������ڶ��ֽ�ͼƬ����������д���������С���ͬʱ���ã��Ե�һ��Ϊ׼��
# ��demoʹ�õ�һ�ַ�ʽ�����ϴ�ͼƬ��ַ�������ʹ�õڶ��ַ�ʽ����ͼƬ����������д�������弴�ɡ�
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
