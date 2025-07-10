"""
阿里云TTS语音合成服务
"""

import http.client
import urllib.parse
import json
import requests
import time
from pathlib import Path
from typing import Tuple, Optional
from config.settings import Settings


class AliTTSService:
    """阿里云TTS语音合成服务类"""
    
    def __init__(self, settings: Settings):
        """初始化阿里云TTS服务"""
        self.settings = settings
        self.host = 'nls-gateway-cn-shanghai.aliyuncs.com'
        self.url_path = '/stream/v1/tts'
        
        # 默认配置
        self.default_config = {
            'appkey': '9C5VYd7UwtTi5xTs',  # 默认AppKey，用户无需配置
            'token': '4615e5a001d4493bae8f9e47ec1de16e',  # 默认Token，用户需要配置
            'voice': 'aitong',
            'format': 'wav',
            'sample_rate': 16000,
            'volume': 50,
            'speech_rate': 0,
            'pitch_rate': 0
        }
        
        # 请求配置
        self.request_config = {
            'timeout': 60,  # 增加超时时间到60秒
            'max_retries': 3,  # 最大重试次数
            'retry_delay': 2   # 重试间隔（秒）
        }
    
    def get_token(self) -> str:
        """获取当前Token"""
        return self.settings.get('aliyun_token', self.default_config['token'])
    
    def set_token(self, token: str):
        """设置Token"""
        self.settings.set('aliyun_token', token)
    
    def get_appkey(self) -> str:
        """获取AppKey（使用默认值）"""
        return self.default_config['appkey']
    
    def build_tts_url(self, text: str, speech_rate: int = 0) -> str:
        """
        构建阿里云TTS请求URL
        
        Args:
            text: 要合成的文本
            speech_rate: 语速，范围是-500~500，默认是0
            
        Returns:
            完整的TTS请求URL
        """
        # 获取配置
        appkey = self.get_appkey()
        token = self.get_token()
        
        # URL编码文本
        text_encoded = self._encode_text(text)
        
        # 构建URL
        url = f'https://{self.host}{self.url_path}'
        url += f'?appkey={appkey}'
        url += f'&token={token}'
        url += f'&text={text_encoded}'
        url += f'&format={self.default_config["format"]}'
        url += f'&sample_rate={self.default_config["sample_rate"]}'
        url += f'&voice={self.default_config["voice"]}'
        url += f'&volume={self.default_config["volume"]}'
        url += f'&speech_rate={speech_rate}'
        url += f'&pitch_rate={self.default_config["pitch_rate"]}'
        
        return url
    
    def download_audio_from_url(self, url: str, output_file: str) -> Tuple[bool, str]:
        """
        从URL下载音频文件（带重试机制）
        
        Args:
            url: 阿里云TTS音频URL
            output_file: 输出文件路径
            
        Returns:
            (成功标志, 错误信息或成功信息)
        """
        for attempt in range(self.request_config['max_retries']):
            try:
                print(f"正在从URL下载音频 (尝试 {attempt + 1}/{self.request_config['max_retries']}): {url[:100]}...")
                
                # 配置请求会话
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                # 使用流式下载，避免大文件内存问题
                response = session.get(
                    url, 
                    timeout=self.request_config['timeout'],
                    stream=True
                )
                response.raise_for_status()
                
                # 检查内容类型
                content_type = response.headers.get('Content-Type', '')
                content_length = response.headers.get('Content-Length', '0')
                print(f'Content-Type: {content_type}')
                print(f'Content-Length: {content_length} bytes')
                
                if 'audio' in content_type or 'application/octet-stream' in content_type:
                    # 保存音频文件
                    output_path = Path(output_file)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 流式写入文件
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    file_size = output_path.stat().st_size
                    print(f"音频文件已保存到: {output_path} ({file_size} bytes)")
                    return True, f"音频文件已保存到: {output_path}"
                else:
                    # 可能是错误响应
                    error_text = response.text[:500] if response.text else "未知错误"
                    print(f"下载失败，响应内容: {error_text}")
                    
                    # 如果是Token过期等错误，不需要重试
                    if 'TokenExpired' in error_text or 'InvalidToken' in error_text:
                        return False, f"Token错误: {error_text}"
                    
                    # 其他错误可能需要重试
                    if attempt < self.request_config['max_retries'] - 1:
                        print(f"等待 {self.request_config['retry_delay']} 秒后重试...")
                        time.sleep(self.request_config['retry_delay'])
                        continue
                    else:
                        return False, f"下载音频失败: {error_text}"
                        
            except requests.exceptions.Timeout:
                error_msg = f"请求超时 ({self.request_config['timeout']}秒)"
                print(f"❌ {error_msg}")
                
                if attempt < self.request_config['max_retries'] - 1:
                    print(f"等待 {self.request_config['retry_delay']} 秒后重试...")
                    time.sleep(self.request_config['retry_delay'])
                    continue
                else:
                    return False, f"网络超时: {error_msg}"
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"网络请求失败: {str(e)}"
                print(f"❌ {error_msg}")
                
                if attempt < self.request_config['max_retries'] - 1:
                    print(f"等待 {self.request_config['retry_delay']} 秒后重试...")
                    time.sleep(self.request_config['retry_delay'])
                    continue
                else:
                    return False, error_msg
                    
            except Exception as e:
                error_msg = f"下载音频文件失败: {str(e)}"
                print(f"❌ {error_msg}")
                
                if attempt < self.request_config['max_retries'] - 1:
                    print(f"等待 {self.request_config['retry_delay']} 秒后重试...")
                    time.sleep(self.request_config['retry_delay'])
                    continue
                else:
                    return False, error_msg
        
        return False, "所有重试均失败"
    
    def synthesize_speech(self, 
                         text: str, 
                         output_file: str,
                         speech_rate: int = 0) -> Tuple[bool, str]:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            output_file: 输出文件路径
            speech_rate: 语速，范围是-500~500，默认是0
            
        Returns:
            (成功标志, 错误信息或成功信息)
        """
        if not text.strip():
            return False, "输入文本不能为空"
        
        try:
            # 构建TTS URL
            tts_url = self.build_tts_url(text, speech_rate)
            print(f"阿里云TTS请求URL: {tts_url[:100]}...")
            
            # 方法1：使用requests直接下载（推荐）
            success, result = self.download_audio_from_url(tts_url, output_file)
            if success:
                return True, result
            
            # 方法2：如果方法1失败，使用原来的http.client方式
            print("使用备用方法重试...")
            return self._synthesize_with_http_client(text, output_file, speech_rate)
            
        except Exception as e:
            return False, f"阿里云TTS语音合成失败: {str(e)}"
    
    def _synthesize_with_http_client(self, text: str, output_file: str, speech_rate: int = 0) -> Tuple[bool, str]:
        """
        使用http.client的备用方法（带超时处理）
        """
        for attempt in range(self.request_config['max_retries']):
            try:
                print(f"HTTP Client方法 (尝试 {attempt + 1}/{self.request_config['max_retries']})")
                
                # 构建请求参数
                params = {
                    'appkey': self.get_appkey(),
                    'token': self.get_token(),
                    'text': text,
                    'format': self.default_config["format"],
                    'sample_rate': self.default_config["sample_rate"],
                    'voice': self.default_config["voice"],
                    'volume': self.default_config["volume"],
                    'speech_rate': speech_rate,
                    'pitch_rate': self.default_config["pitch_rate"]
                }
                
                # 构建查询字符串
                query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
                request_url = f'{self.url_path}?{query_string}'
                
                print(f"HTTP Client请求URL: https://{self.host}{request_url[:100]}...")
                
                # 发送请求
                conn = http.client.HTTPSConnection(self.host, timeout=self.request_config['timeout'])
                conn.request(method='GET', url=request_url)
                
                # 处理响应
                response = conn.getresponse()
                print(f'阿里云TTS响应状态: {response.status} {response.reason}')
                
                content_type = response.getheader('Content-Type')
                print(f'Content-Type: {content_type}')
                
                body = response.read()
                
                if response.status == 200 and ('audio' in content_type or 'application/octet-stream' in content_type):
                    # 保存音频文件
                    output_path = Path(output_file)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_path, mode='wb') as f:
                        f.write(body)
                    
                    conn.close()
                    file_size = output_path.stat().st_size
                    print(f"音频文件已保存到: {output_path} ({file_size} bytes)")
                    return True, f"音频文件已保存到: {output_path}"
                else:
                    conn.close()
                    error_msg = body.decode('utf-8') if body else f"HTTP {response.status}: {response.reason}"
                    print(f"❌ HTTP Client失败: {error_msg}")
                    
                    # 如果是Token错误，不需要重试
                    if 'TokenExpired' in error_msg or 'InvalidToken' in error_msg:
                        return False, f"Token错误: {error_msg}"
                    
                    if attempt < self.request_config['max_retries'] - 1:
                        print(f"等待 {self.request_config['retry_delay']} 秒后重试...")
                        time.sleep(self.request_config['retry_delay'])
                        continue
                    else:
                        return False, f"阿里云TTS请求失败: {error_msg}"
                        
            except Exception as e:
                error_msg = f"HTTP Client方法失败: {str(e)}"
                print(f"❌ {error_msg}")
                
                if attempt < self.request_config['max_retries'] - 1:
                    print(f"等待 {self.request_config['retry_delay']} 秒后重试...")
                    time.sleep(self.request_config['retry_delay'])
                    continue
                else:
                    return False, error_msg
        
        return False, "所有重试均失败"
    
    def _encode_text(self, text: str) -> str:
        """对文本进行URL编码"""
        # 采用RFC 3986规范进行urlencode编码
        text_encoded = urllib.parse.quote_plus(text)
        text_encoded = text_encoded.replace("+", "%20")
        text_encoded = text_encoded.replace("*", "%2A")
        text_encoded = text_encoded.replace("%7E", "~")
        return text_encoded
    
    def test_synthesis(self, text: str = "这是一个测试") -> bool:
        """测试语音合成功能"""
        try:
            test_file = Path.home() / "test_alitts.wav"
            
            success, _ = self.synthesize_speech(
                text=text,
                output_file=str(test_file),
                speech_rate=0
            )
            
            if success and test_file.exists():
                test_file.unlink()  # 删除测试文件
                return True
            return False
        except Exception:
            return False
    
    def test_url_generation(self, text: str = "这是一个测试") -> str:
        """测试URL生成功能，返回生成的URL"""
        try:
            return self.build_tts_url(text, 0)
        except Exception as e:
            return f"URL生成失败: {str(e)}"
    
    def _convert_speed_to_rate(self, ui_speed: float) -> int:
        """
        将UI语速转换为阿里云TTS的speech_rate
        
        UI语速范围: 1.0-2.0 (1.0x-2.0x)
        阿里云speech_rate范围: 0-500 (0对应1.0x，500对应2.0x)
        """
        # 将1.0-2.0的范围映射到0-500
        rate = int((ui_speed - 1.0) * 500)
        
        # 确保在有效范围内
        rate = max(0, min(500, rate))
        
        return rate
    
    def is_available(self) -> bool:
        """检查阿里云TTS服务是否可用"""
        token = self.get_token()
        
        if not token:
            return False
        
        # 可以进一步测试连接
        return True 