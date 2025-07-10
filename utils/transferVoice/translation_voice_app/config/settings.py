"""
应用程序配置管理
"""

import os
import json
from pathlib import Path
from typing import Dict, Any


class Settings:
    """应用程序设置管理器"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.app_dir = self.config_dir.parent
        self.root_dir = self.app_dir.parent
        
        # 百度翻译API配置
        self.baidu_appid = '20250521002362210'
        self.baidu_key = 'H7CKQfnbFrqdqxTmv5MR'
        
        # Google TTS配置
        self.google_credentials_file = self.config_dir / 'google_credentials.json'
        
        # 语言配置
        self.languages_file = self.config_dir / 'languages.json'
        
        # 用户设置文件
        self.user_settings_file = self.config_dir / 'user_settings.json'
        
        # 默认设置
        self.default_settings = {
            'last_save_path': str(Path.home() / 'Downloads'),
            'voice_type': 'girl',  # boy, girl, danbao, aitong
            'speech_rate': 1.0,
            'audio_format': 'wav',
            'window_geometry': None,
            'source_language': 'zh-cn',
            'target_language': 'en',
            'aliyun_appkey': '',
            'aliyun_token': ''
        }
        
        # 加载用户设置
        self.user_settings = self.load_user_settings()
    
    def load_user_settings(self) -> Dict[str, Any]:
        """加载用户设置"""
        if self.user_settings_file.exists():
            try:
                with open(self.user_settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                # 合并默认设置和用户设置
                merged_settings = self.default_settings.copy()
                merged_settings.update(settings)
                return merged_settings
            except Exception as e:
                print(f"加载用户设置失败: {e}")
                return self.default_settings.copy()
        else:
            return self.default_settings.copy()
    
    def save_user_settings(self):
        """保存用户设置"""
        try:
            with open(self.user_settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户设置失败: {e}")
    
    def get(self, key: str, default=None):
        """获取设置值"""
        return self.user_settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置值"""
        # 特殊处理QByteArray类型（窗口几何信息）
        if hasattr(value, 'data') and hasattr(value, 'toBase64'):
            # 这是QByteArray，转换为base64字符串
            value = value.toBase64().data().decode('utf-8')
        
        self.user_settings[key] = value
        self.save_user_settings()
    
    def load_languages(self) -> Dict[str, Any]:
        """加载语言配置"""
        try:
            with open(self.languages_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载语言配置失败: {e}")
            # 返回默认语言配置
            return {
                "supported": [
                    {"code": "zh-cn", "name": "中文", "direction": "source", "enabled": True},
                    {"code": "en", "name": "English", "direction": "target", "enabled": True}
                ],
                "upcoming": [],
                "default_source": "zh-cn",
                "default_target": "en"
            }
    
    def setup_google_credentials(self):
        """设置Google凭据环境变量"""
        if self.google_credentials_file.exists():
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(self.google_credentials_file)
            return True
        return False
    
    @property
    def voice_types(self):
        """语音类型映射"""
        return {
            'boy': 'en-US-Wavenet-I',
            'girl': 'en-US-Wavenet-F',
            'danbao': 'en-US-Wavenet-F',
            'aitong': 'aliyun-aitong'  # 阿里云艾彤发音人
        } 