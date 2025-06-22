#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件处理服务 - 解决中文编码问题
"""

import pandas as pd
import chardet
import io
from typing import List, Dict, Union
import logging

logger = logging.getLogger(__name__)

class ExcelProcessor:
    """Excel文件处理器，专门处理编码问题"""
    
    @staticmethod
    def detect_encoding(file_content: bytes) -> str:
        """
        检测文件编码
        
        Args:
            file_content: 文件二进制内容
            
        Returns:
            str: 检测到的编码格式
        """
        try:
            # 使用chardet库检测编码
            detected = chardet.detect(file_content)
            encoding = detected.get('encoding', 'utf-8')
            confidence = detected.get('confidence', 0)
            
            logger.info(f"检测到编码: {encoding}, 置信度: {confidence}")
            
            # 如果置信度过低，尝试常见的中文编码
            if confidence < 0.7:
                common_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
                for enc in common_encodings:
                    try:
                        test_content = file_content.decode(enc)
                        # 检查中文字符比例
                        chinese_chars = len([c for c in test_content if '\u4e00' <= c <= '\u9fff'])
                        if chinese_chars > 0:
                            logger.info(f"通过中文字符验证，使用编码: {enc}")
                            return enc
                    except UnicodeDecodeError:
                        continue
            
            return encoding if encoding else 'utf-8'
            
        except Exception as e:
            logger.warning(f"编码检测失败: {e}, 使用默认UTF-8")
            return 'utf-8'
    
    @staticmethod
    def read_excel_with_encoding_detection(file_path_or_buffer: Union[str, bytes, io.BytesIO], 
                                         sheet_name=0) -> pd.DataFrame:
        """
        读取Excel文件，自动处理编码问题
        
        Args:
            file_path_or_buffer: 文件路径、二进制内容或BytesIO对象
            sheet_name: 工作表名称或索引
            
        Returns:
            pd.DataFrame: 读取的数据
        """
        try:
            # 如果是路径字符串，直接读取
            if isinstance(file_path_or_buffer, str):
                return pd.read_excel(file_path_or_buffer, sheet_name=sheet_name, engine='openpyxl')
            
            # 如果是bytes或BytesIO，需要处理编码
            if isinstance(file_path_or_buffer, bytes):
                file_buffer = io.BytesIO(file_path_or_buffer)
            else:
                file_buffer = file_path_or_buffer
            
            # 尝试使用openpyxl引擎读取
            try:
                df = pd.read_excel(file_buffer, sheet_name=sheet_name, engine='openpyxl')
                return df
            except Exception as e:
                logger.warning(f"openpyxl引擎读取失败: {e}")
            
            # 如果openpyxl失败，尝试xlrd引擎（针对老版本Excel）
            try:
                file_buffer.seek(0)
                df = pd.read_excel(file_buffer, sheet_name=sheet_name, engine='xlrd')
                return df
            except Exception as e:
                logger.warning(f"xlrd引擎读取失败: {e}")
            
            # 都失败了，抛出异常
            raise Exception("无法使用任何引擎读取Excel文件")
            
        except Exception as e:
            logger.error(f"Excel文件读取失败: {e}")
            raise
    
    @staticmethod
    def extract_test_data_from_excel(file_content: Union[str, bytes, io.BytesIO], 
                                   text_column: Union[str, int] = 0) -> List[Dict[str, str]]:
        """
        从Excel文件中提取测试数据
        
        Args:
            file_content: Excel文件内容
            text_column: 文本列名或列索引
            
        Returns:
            List[Dict[str, str]]: 测试数据列表
        """
        try:
            # 读取Excel文件
            df = ExcelProcessor.read_excel_with_encoding_detection(file_content)
            
            # 如果DataFrame为空
            if df.empty:
                logger.warning("Excel文件为空")
                return []
            
            # 获取文本列
            if isinstance(text_column, int):
                if text_column >= len(df.columns):
                    logger.error(f"列索引 {text_column} 超出范围")
                    return []
                text_series = df.iloc[:, text_column]
            else:
                if text_column not in df.columns:
                    logger.error(f"未找到列 '{text_column}'")
                    return []
                text_series = df[text_column]
            
            # 提取有效的测试文本
            test_data = []
            for idx, text in text_series.items():
                if pd.notna(text):
                    text_str = str(text).strip()
                    # 跳过标题行和空行
                    if (text_str and 
                        text_str not in ['测试文本', 'text', '文本内容', 'Test Text'] and
                        len(text_str) > 0):
                        
                        # 验证是否包含有效字符（中文、英文、数字）
                        if any(c.isalnum() or '\u4e00' <= c <= '\u9fff' for c in text_str):
                            test_data.append({'text': text_str})
            
            logger.info(f"成功提取 {len(test_data)} 条测试数据")
            return test_data
            
        except Exception as e:
            logger.error(f"提取测试数据失败: {e}")
            raise
    
    @staticmethod
    def validate_and_clean_text(text: str) -> str:
        """
        验证和清理文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""
        
        # 移除前后空白
        cleaned = text.strip()
        
        # 移除控制字符
        cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\t\n\r')
        
        # 检查是否包含有效字符
        has_valid_chars = any(c.isalnum() or '\u4e00' <= c <= '\u9fff' for c in cleaned)
        
        return cleaned if has_valid_chars else ""
    
    @staticmethod
    def convert_csv_encoding(file_content: bytes, target_encoding: str = 'utf-8') -> str:
        """
        转换CSV文件编码
        
        Args:
            file_content: CSV文件二进制内容
            target_encoding: 目标编码
            
        Returns:
            str: 转换后的文本内容
        """
        try:
            # 检测原始编码
            source_encoding = ExcelProcessor.detect_encoding(file_content)
            
            # 解码并重新编码
            text_content = file_content.decode(source_encoding)
            
            # 验证和清理每行文本
            lines = text_content.split('\n')
            cleaned_lines = []
            
            for line in lines:
                cleaned_line = ExcelProcessor.validate_and_clean_text(line)
                if cleaned_line:
                    cleaned_lines.append(cleaned_line)
            
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            logger.error(f"CSV编码转换失败: {e}")
            raise 