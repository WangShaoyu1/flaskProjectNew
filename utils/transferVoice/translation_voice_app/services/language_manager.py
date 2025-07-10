"""
语言管理服务
"""

from typing import Dict, List, Any, Tuple
from config.settings import Settings


class LanguageManager:
    """语言管理器"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.languages_config = settings.load_languages()
    
    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """获取支持的语言列表"""
        return self.languages_config.get('supported', [])
    
    def get_upcoming_languages(self) -> List[Dict[str, Any]]:
        """获取即将支持的语言列表"""
        return self.languages_config.get('upcoming', [])
    
    def get_source_languages(self) -> List[Dict[str, Any]]:
        """获取源语言列表"""
        supported = self.get_supported_languages()
        return [lang for lang in supported if lang.get('direction') == 'source' and lang.get('enabled', False)]
    
    def get_target_languages(self, include_upcoming: bool = True) -> List[Dict[str, Any]]:
        """
        获取目标语言列表
        
        Args:
            include_upcoming: 是否包含即将支持的语言
            
        Returns:
            目标语言列表
        """
        # 支持的目标语言
        supported = self.get_supported_languages()
        target_langs = [lang for lang in supported if lang.get('direction') == 'target' and lang.get('enabled', False)]
        
        if include_upcoming:
            # 添加即将支持的语言
            upcoming = self.get_upcoming_languages()
            target_langs.extend(upcoming)
        
        return target_langs
    
    def is_language_supported(self, language_code: str) -> bool:
        """
        检查语言是否支持
        
        Args:
            language_code: 语言代码
            
        Returns:
            是否支持该语言
        """
        supported = self.get_supported_languages()
        for lang in supported:
            if lang.get('code') == language_code and lang.get('enabled', False):
                return True
        return False
    
    def get_language_name(self, language_code: str) -> str:
        """
        根据语言代码获取语言名称
        
        Args:
            language_code: 语言代码
            
        Returns:
            语言名称
        """
        all_languages = self.get_supported_languages() + self.get_upcoming_languages()
        for lang in all_languages:
            if lang.get('code') == language_code:
                return lang.get('name', language_code)
        return language_code
    
    def get_default_languages(self) -> Tuple[str, str]:
        """
        获取默认的源语言和目标语言
        
        Returns:
            (源语言代码, 目标语言代码)
        """
        default_source = self.languages_config.get('default_source', 'zh-cn')
        default_target = self.languages_config.get('default_target', 'en')
        return default_source, default_target
    
    def get_translation_pairs(self) -> List[Tuple[str, str]]:
        """
        获取支持的翻译语言对
        
        Returns:
            支持的翻译对列表 [(源语言, 目标语言), ...]
        """
        source_langs = self.get_source_languages()
        target_langs = [lang for lang in self.get_target_languages(include_upcoming=False)]
        
        pairs = []
        for source in source_langs:
            for target in target_langs:
                pairs.append((source['code'], target['code']))
        
        return pairs
    
    def validate_translation_pair(self, source_code: str, target_code: str) -> bool:
        """
        验证翻译语言对是否支持
        
        Args:
            source_code: 源语言代码
            target_code: 目标语言代码
            
        Returns:
            是否支持该翻译对
        """
        supported_pairs = self.get_translation_pairs()
        return (source_code, target_code) in supported_pairs
    
    def get_language_info(self, language_code: str) -> Dict[str, Any]:
        """
        获取语言详细信息
        
        Args:
            language_code: 语言代码
            
        Returns:
            语言信息字典
        """
        all_languages = self.get_supported_languages() + self.get_upcoming_languages()
        for lang in all_languages:
            if lang.get('code') == language_code:
                return lang.copy()
        
        # 如果没找到，返回默认信息
        return {
            'code': language_code,
            'name': language_code,
            'direction': 'unknown',
            'enabled': False
        }
    
    def format_language_display(self, language_code: str) -> str:
        """
        格式化语言显示名称
        
        Args:
            language_code: 语言代码
            
        Returns:
            格式化后的显示名称
        """
        lang_info = self.get_language_info(language_code)
        name = lang_info.get('name', language_code)
        
        if not lang_info.get('enabled', True):
            tooltip = lang_info.get('tooltip', '暂不支持')
            return f"{name} ({tooltip})"
        
        return name
    
    def get_tts_language_code(self, language_code: str) -> str:
        """
        获取TTS服务对应的语言代码
        
        Args:
            language_code: 应用内语言代码
            
        Returns:
            TTS服务的语言代码
        """
        # 语言代码映射表
        tts_mapping = {
            'zh-cn': 'zh-CN',
            'en': 'en-US',
            'ja': 'ja-JP',
            'ko': 'ko-KR',
            'fr': 'fr-FR'
        }
        
        return tts_mapping.get(language_code, 'en-US')
    
    def get_translation_service_codes(self, language_code: str) -> str:
        """
        获取翻译服务对应的语言代码
        
        Args:
            language_code: 应用内语言代码
            
        Returns:
            翻译服务的语言代码
        """
        # 百度翻译语言代码映射
        baidu_mapping = {
            'zh-cn': 'zh',
            'en': 'en',
            'ja': 'jp',
            'ko': 'kor',
            'fr': 'fra'
        }
        
        return baidu_mapping.get(language_code, language_code) 