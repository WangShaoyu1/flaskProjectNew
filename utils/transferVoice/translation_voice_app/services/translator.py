"""
翻译服务 - 基于百度翻译API
"""

import requests
import hashlib
import time
from typing import List, Tuple, Optional
from config.settings import Settings


class TranslatorService:
    """翻译服务类"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.appid = settings.baidu_appid
        self.key = settings.baidu_key
        self.endpoint = 'http://api.fanyi.baidu.com'
        self.path = '/api/trans/vip/translate'
        self.url = self.endpoint + self.path
    
    def _make_md5(self, s: str, encoding='utf-8') -> str:
        """生成MD5签名"""
        return hashlib.md5(s.encode(encoding)).hexdigest()
    
    def translate_single(self, text: str, from_lang='zh', to_lang='en') -> Tuple[bool, str]:
        """
        翻译单条文本
        
        Args:
            text: 要翻译的文本
            from_lang: 源语言代码
            to_lang: 目标语言代码
            
        Returns:
            (成功标志, 翻译结果或错误信息)
        """
        try:
            # 生成salt和sign
            salt = str(int(time.time() * 1000))
            sign = self._make_md5(self.appid + text + salt + self.key)
            
            # 构建请求参数
            params = {
                'appid': self.appid,
                'q': text,
                'from': from_lang,
                'to': to_lang,
                'salt': salt,
                'sign': sign
            }
            
            # 发送请求
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            response = requests.post(self.url, params=params, headers=headers, timeout=10)
            result = response.json()
            
            # 检查响应
            if 'trans_result' in result:
                # 提取翻译结果
                translations = []
                for item in result['trans_result']:
                    translations.append(item['dst'])
                return True, '\n'.join(translations)
            else:
                error_msg = result.get('error_msg', '翻译失败')
                return False, f"翻译错误: {error_msg}"
                
        except requests.exceptions.RequestException as e:
            return False, f"网络请求失败: {str(e)}"
        except Exception as e:
            return False, f"翻译过程中发生错误: {str(e)}"
    
    def translate_multiple(self, texts: List[str], from_lang='zh', to_lang='en') -> List[Tuple[bool, str]]:
        """
        批量翻译多条文本
        
        Args:
            texts: 要翻译的文本列表
            from_lang: 源语言代码
            to_lang: 目标语言代码
            
        Returns:
            翻译结果列表，每个元素为(成功标志, 翻译结果或错误信息)
        """
        results = []
        for text in texts:
            if text.strip():  # 跳过空文本
                result = self.translate_single(text.strip(), from_lang, to_lang)
                results.append(result)
                # 避免请求过于频繁
                time.sleep(0.1)
            else:
                results.append((True, ""))
        return results
    
    def translate_text(self, text: str, from_lang='zh', to_lang='en') -> Tuple[bool, str]:
        """
        翻译文本（支持多行）
        
        Args:
            text: 要翻译的文本（可包含换行符）
            from_lang: 源语言代码
            to_lang: 目标语言代码
            
        Returns:
            (成功标志, 翻译结果或错误信息)
        """
        if not text.strip():
            return False, "输入文本不能为空"
        
        # 分割多行文本
        lines = text.split('\n')
        if len(lines) == 1:
            # 单行文本
            return self.translate_single(text.strip(), from_lang, to_lang)
        else:
            # 多行文本
            results = self.translate_multiple(lines, from_lang, to_lang)
            
            # 检查是否所有翻译都成功
            all_success = all(success for success, _ in results)
            if all_success:
                translated_lines = [result for _, result in results]
                return True, '\n'.join(translated_lines)
            else:
                # 收集错误信息
                error_lines = []
                for i, (success, result) in enumerate(results):
                    if not success:
                        error_lines.append(f"第{i+1}行: {result}")
                return False, "部分翻译失败:\n" + '\n'.join(error_lines)
    
    def test_connection(self) -> bool:
        """测试翻译服务连接"""
        try:
            success, _ = self.translate_single("测试", "zh", "en")
            return success
        except Exception:
            return False 