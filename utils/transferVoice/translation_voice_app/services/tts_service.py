"""
TTS语音合成服务 - 基于Google Text-to-Speech API
"""

import os
import io
from pathlib import Path
from typing import List, Tuple, Optional
from google.cloud import texttospeech
from config.settings import Settings


class TTSService:
    """文本转语音服务类"""
    
    def __init__(self, settings: Settings):
        """初始化TTS服务"""
        self.settings = settings
        self.client = None
        self._is_available = False
        
        # 尝试初始化Google TTS客户端
        self._init_client()
    
    def _init_client(self):
        """初始化Google TTS客户端"""
        try:
            # 检查凭据文件
            credentials_file = self.settings.get("google_credentials_file")
            if not credentials_file:
                credentials_file = Path(__file__).parent.parent / "config" / "google_credentials.json"
            
            credentials_path = Path(credentials_file)
            
            if not credentials_path.exists():
                print(f"警告: Google TTS凭据文件不存在: {credentials_path}")
                print("请将您的Google服务账户凭据文件放置在 config/google_credentials.json")
                print("或通过设置界面指定凭据文件路径")
                self._is_available = False
                return
            
            # 设置环境变量
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_path)
            
            # 初始化客户端
            self.client = texttospeech.TextToSpeechClient()
            self._is_available = True
            print("Google TTS客户端初始化成功")
            
        except Exception as e:
            print(f"初始化Google TTS客户端失败: {str(e)}")
            print("TTS功能将不可用，请检查Google凭据配置")
            self._is_available = False
            self.client = None
    
    def is_available(self) -> bool:
        """检查TTS服务是否可用"""
        return self._is_available
    
    def synthesize_speech(self, 
                         text: str, 
                         output_file: str,
                         voice_type: str = 'girl',
                         speech_rate: float = 1.0,
                         language_code: str = 'en-US') -> Tuple[bool, str]:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            output_file: 输出文件路径
            voice_type: 语音类型 (boy, girl, danbao)
            speech_rate: 语速 (0.25-4.0)
            language_code: 语言代码
            
        Returns:
            (成功标志, 错误信息或成功信息)
        """
        if not self.client:
            return False, "TTS服务未初始化"
        
        if not text.strip():
            return False, "输入文本不能为空"
        
        try:
            # 获取语音名称
            voice_name = self.settings.voice_types.get(voice_type, 'en-US-Wavenet-F')
            
            # 构建合成请求
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE if voice_type in ['girl', 'danbao'] else texttospeech.SsmlVoiceGender.MALE
            )
            
            # 音频配置 - 输出WAV格式
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,  # WAV格式
                speaking_rate=speech_rate
            )
            
            # 执行合成
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # 保存音频文件
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            
            return True, f"音频文件已保存到: {output_path}"
            
        except Exception as e:
            return False, f"语音合成失败: {str(e)}"
    
    def synthesize_multiple(self,
                           texts: List[str],
                           output_dir: str,
                           voice_type: str = 'girl',
                           speech_rate: float = 1.0,
                           language_code: str = 'en-US',
                           filename_prefix: str = 'audio') -> List[Tuple[bool, str]]:
        """
        批量合成语音
        
        Args:
            texts: 要合成的文本列表
            output_dir: 输出目录
            voice_type: 语音类型
            speech_rate: 语速
            language_code: 语言代码
            filename_prefix: 文件名前缀
            
        Returns:
            合成结果列表
        """
        results = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for i, text in enumerate(texts):
            if text.strip():  # 跳过空文本
                filename = f"{filename_prefix}_{i+1:03d}.wav"
                output_file = output_path / filename
                
                result = self.synthesize_speech(
                    text=text.strip(),
                    output_file=str(output_file),
                    voice_type=voice_type,
                    speech_rate=speech_rate,
                    language_code=language_code
                )
                results.append(result)
            else:
                results.append((True, "跳过空文本"))
        
        return results
    
    def get_available_voices(self, language_code: str = 'en-US') -> List[dict]:
        """获取可用的语音列表"""
        if not self.client:
            return []
        
        try:
            voices = self.client.list_voices(language_code=language_code)
            return [
                {
                    'name': voice.name,
                    'language': voice.language_codes[0],
                    'gender': voice.ssml_gender.name
                }
                for voice in voices.voices
            ]
        except Exception as e:
            print(f"获取语音列表失败: {e}")
            return []
    
    def test_synthesis(self) -> bool:
        """测试语音合成功能"""
        try:
            test_text = "This is a test."
            test_file = Path.home() / "test_tts.wav"
            
            success, _ = self.synthesize_speech(
                text=test_text,
                output_file=str(test_file),
                voice_type='girl'
            )
            
            if success and test_file.exists():
                test_file.unlink()  # 删除测试文件
                return True
            return False
        except Exception:
            return False 