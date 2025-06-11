import os
import time
import json
import hashlib
import requests
from enum import Enum
from pathlib import Path
from pydub import AudioSegment
import speech_recognition as sr
from google.cloud import texttospeech
from functools import wraps

# ===== 配置部分 =====
BAIDU_APPID = '20250521002362210'
BAIDU_KEY = 'H7CKQfnbFrqdqxTmv5MR'
INPUT_CHINESE_FOLDER = './input_chinese'
OUTPUT_ENGLISH_FOLDER = './output_english'
LOG_FILE = './log.txt'  # 日志文件
RECOGNITION_TXT = './recognition.txt'  # 识别的中文、翻译后的英文
SPEECH_TO_TEXT_STATE = False  # 是否开展语音转文本状态
FLIE_LANGUAGE_TEXT_DICT = {}  # 语言文本字典
FLIE_LANGUAGE_TEXT_DICT_PATH = './language_text_dict.json'  # 语言文本字典文件路径


# ===== 语音类型枚举 =====
class VoiceType(Enum):
    boy = "en-US-Wavenet-I"
    girl = "en-US-Wavenet-F"
    danbao = "en-US-Wavenet-F"
    unknown = "en-US-Wavenet-F"


# ===== 耗时统计装饰器 =====
def timeit(func):
    """高精度耗时统计装饰器[6,8](@ref)"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = (time.perf_counter() - start) * 1000
        print(f"[{func.__name__}] 耗时：{duration:.2f} ms")
        return result

    return wrapper


# ===== 核心功能模块 =====
@timeit
def speech_to_text(audio_path):
    """语音转文本（中文）"""
    try:
        audio = AudioSegment.from_file(audio_path)
        wav_path = audio_path.replace(Path(audio_path).suffix, '_temp.wav')
        audio.export(wav_path, format="wav")

        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language='zh-CN')
        os.remove(wav_path)
        return text
    except Exception as e:
        print(f"识别失败：{str(e)}")
        return ""


@timeit
def translate(text):
    """文本翻译（中->英）"""
    url = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
    salt = '12345'
    sign = hashlib.md5((BAIDU_APPID + text + salt + BAIDU_KEY).encode()).hexdigest()

    params = {
        'q': text,
        'from': 'zh',
        'to': 'en',
        'appid': BAIDU_APPID,
        'salt': salt,
        'sign': sign
    }
    response = requests.get(url, params=params)
    return "".join(item['dst'] for item in response.json()['trans_result'])


@timeit
def google_tts(text, output_file, lang="en-US", voice_name="en-US-Wavenet-F"):
    """文本转语音（支持逐行处理）[9](@ref)"""
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang,
        name=voice_name,
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        speaking_rate=1.15
    )
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    with open(output_file, "wb") as out:
        out.write(response.audio_content)


# ===== 处理英文JSON文件 =====
def process_english_json(json_file_path):
    """
    从指定JSON文件生成语音
    :param json_file_path: JSON文件完整路径
    """
    # 确保输出目录存在
    os.makedirs(OUTPUT_ENGLISH_FOLDER, exist_ok=True)

    try:
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 处理每个键值对
        for key, value in data.items():
            if isinstance(value, dict) and 'english' in value:
                # 生成输出文件路径
                output_path = os.path.join(
                    OUTPUT_ENGLISH_FOLDER,
                    f"{Path(key).stem}_en.mp3"
                )

                # 生成语音文件
                google_tts(text=value['english'], output_file=output_path,
                           voice_name=VoiceType[value.get('tone', 'unknown')].value)
                print(f"已生成: {output_path}")

    except json.JSONDecodeError:
        print(f"错误：文件 '{json_file_path}' 不是有效的JSON格式")
    except KeyError as e:
        print(f"错误：JSON数据缺少必要的'english'字段")
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")


# ===== 主处理流程 =====
def main():
    if SPEECH_TO_TEXT_STATE:
        # 处理中文音频
        os.makedirs(OUTPUT_ENGLISH_FOLDER, exist_ok=True)
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write("文件名---识别内容\n")

        # 处理中文音频文件
        for filename in os.listdir(INPUT_CHINESE_FOLDER):
            if filename.lower().endswith(('.mp3', '.wav', '.m4a')):
                file_start = time.perf_counter()
                input_path = os.path.join(INPUT_CHINESE_FOLDER, filename)
                base_name = os.path.splitext(filename)[0]
                voice_type = None  # 音色类型
                # 识别中文音频
                chinese_text = speech_to_text(input_path)
                # 翻译中文文本为英文文本
                english_text = translate(chinese_text)
                # 生成英文语音
                output_base = os.path.join(OUTPUT_ENGLISH_FOLDER, base_name)
                google_tts(english_text, f"{output_base}_en.mp3")

                # 记录日志
                with open(LOG_FILE, 'a', encoding='utf-8') as log:
                    log.write(f"{filename}---{chinese_text}---{english_text}\n")
                    log.write(f"总耗时：{(time.perf_counter() - file_start) * 1000:.2f} ms\n")
                # 记录识别的中文和翻译后的英文
                with open(f"{RECOGNITION_TXT}", 'a', encoding='utf-8') as f:
                    f.write(f"{filename}---{chinese_text}---{english_text}\n")

                # 记录语言文本字典
                for keyword in ['boy', 'danbao', 'girl']:
                    if keyword in filename.lower():
                        voice_type = keyword
                        break
                FLIE_LANGUAGE_TEXT_DICT[filename] = {
                    "chinese": chinese_text,
                    "english": english_text,
                    "tone": voice_type or "unknown"
                }
    else:
        # 处理英文JSON文件
        if os.path.exists(FLIE_LANGUAGE_TEXT_DICT_PATH):
            process_english_json(FLIE_LANGUAGE_TEXT_DICT_PATH)


if __name__ == "__main__":
    total_start = time.perf_counter()
    main()
    print(f"\n总耗时：{(time.perf_counter() - total_start):.2f} s")

    if not os.path.exists(FLIE_LANGUAGE_TEXT_DICT_PATH):
        # 记录识别的中文和翻译后的英文
        with open(f"{FLIE_LANGUAGE_TEXT_DICT_PATH}", 'w', encoding='utf-8') as f:
            json.dump(FLIE_LANGUAGE_TEXT_DICT, f, ensure_ascii=False, indent=4)
