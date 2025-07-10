"""
测试文件处理服务
用于处理批量测试的Excel和CSV文件
"""

import pandas as pd
import json
import logging
from typing import List, Dict, Any, Optional
from io import BytesIO
import os

logger = logging.getLogger(__name__)

class TestFileProcessor:
    """测试文件处理器"""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv']
        self.required_columns = ['text']  # 必需的列
        self.optional_columns = ['expected_intent', 'expected_entities', 'description']
    
    def validate_file_format(self, filename: str) -> bool:
        """验证文件格式"""
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in self.supported_formats
    
    def read_test_file(self, file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        """读取测试文件"""
        try:
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext in ['.xlsx', '.xls']:
                return self._read_excel_file(file_content)
            elif file_ext == '.csv':
                return self._read_csv_file(file_content)
            else:
                raise ValueError(f"不支持的文件格式: {file_ext}")
                
        except Exception as e:
            logger.error(f"读取测试文件失败: {e}")
            raise
    
    def _read_excel_file(self, file_content: bytes) -> List[Dict[str, Any]]:
        """读取Excel文件"""
        try:
            # 使用BytesIO读取Excel文件
            excel_file = BytesIO(file_content)
            df = pd.read_excel(excel_file, sheet_name=0)
            
            return self._process_dataframe(df)
            
        except Exception as e:
            logger.error(f"读取Excel文件失败: {e}")
            raise ValueError(f"Excel文件格式错误: {e}")
    
    def _read_csv_file(self, file_content: bytes) -> List[Dict[str, Any]]:
        """读取CSV文件"""
        try:
            # 使用BytesIO读取CSV文件
            csv_file = BytesIO(file_content)
            df = pd.read_csv(csv_file, encoding='utf-8')
            
            return self._process_dataframe(df)
            
        except UnicodeDecodeError:
            # 尝试使用GBK编码
            try:
                csv_file = BytesIO(file_content)
                df = pd.read_csv(csv_file, encoding='gbk')
                return self._process_dataframe(df)
            except Exception as e:
                logger.error(f"读取CSV文件失败(GBK): {e}")
                raise ValueError(f"CSV文件编码错误: {e}")
        except Exception as e:
            logger.error(f"读取CSV文件失败: {e}")
            raise ValueError(f"CSV文件格式错误: {e}")
    
    def _process_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """处理DataFrame数据"""
        # 验证必需的列
        if 'text' not in df.columns:
            raise ValueError("文件中必须包含'text'列")
        
        # 清理数据
        df = df.dropna(subset=['text'])  # 删除text为空的行
        df['text'] = df['text'].astype(str).str.strip()  # 清理文本
        df = df[df['text'] != '']  # 删除空文本行
        
        # 转换为字典列表
        test_data = []
        for _, row in df.iterrows():
            item = {
                'text': row['text']
            }
            
            # 添加可选字段
            if 'expected_intent' in df.columns and pd.notna(row['expected_intent']):
                item['expected_intent'] = str(row['expected_intent']).strip()
            
            if 'expected_entities' in df.columns and pd.notna(row['expected_entities']):
                # 尝试解析JSON格式的实体
                try:
                    entities = json.loads(str(row['expected_entities']))
                    item['expected_entities'] = entities
                except (json.JSONDecodeError, ValueError):
                    # 如果不是JSON格式，作为字符串处理
                    item['expected_entities'] = str(row['expected_entities']).strip()
            
            if 'description' in df.columns and pd.notna(row['description']):
                item['description'] = str(row['description']).strip()
            
            test_data.append(item)
        
        if not test_data:
            raise ValueError("文件中没有有效的测试数据")
        
        return test_data
    
    def validate_test_data(self, test_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证测试数据"""
        validation_result = {
            'is_valid': True,
            'total_count': len(test_data),
            'valid_count': 0,
            'invalid_count': 0,
            'errors': []
        }
        
        valid_items = []
        
        for i, item in enumerate(test_data):
            row_errors = []
            
            # 验证text字段
            if not item.get('text') or not item['text'].strip():
                row_errors.append(f"第{i+1}行: 测试文本不能为空")
            elif len(item['text']) > 1000:
                row_errors.append(f"第{i+1}行: 测试文本过长(超过1000字符)")
            
            # 验证expected_intent字段
            if 'expected_intent' in item and item['expected_intent']:
                if len(item['expected_intent']) > 100:
                    row_errors.append(f"第{i+1}行: 期望意图名称过长")
            
            if row_errors:
                validation_result['errors'].extend(row_errors)
                validation_result['invalid_count'] += 1
            else:
                valid_items.append(item)
                validation_result['valid_count'] += 1
        
        # 更新验证结果
        validation_result['is_valid'] = validation_result['invalid_count'] == 0
        validation_result['valid_data'] = valid_items
        
        return validation_result
    
    def generate_test_template(self) -> pd.DataFrame:
        """生成测试模板"""
        template_data = {
            'text': [
                '设置温度为25度',
                '播放音乐',
                '查询天气',
                '开启空调',
                '关闭灯光'
            ],
            'expected_intent': [
                'set_temperature',
                'play_music',
                'query_weather',
                'turn_on_ac',
                'turn_off_light'
            ],
            'expected_entities': [
                '[{"entity": "temperature", "value": "25"}]',
                '[]',
                '[]',
                '[]',
                '[]'
            ],
            'description': [
                '设置温度指令测试',
                '播放音乐指令测试',
                '天气查询指令测试',
                '开启空调指令测试',
                '关闭灯光指令测试'
            ]
        }
        
        return pd.DataFrame(template_data)
    
    def export_test_results(self, test_results: List[Dict[str, Any]]) -> bytes:
        """导出测试结果"""
        try:
            # 准备导出数据
            export_data = []
            for result in test_results:
                row = {
                    '测试文本': result.get('input_text', ''),
                    '期望意图': result.get('expected_intent', ''),
                    '实际意图': result.get('actual_intent', ''),
                    '置信度': result.get('confidence_score', 0),
                    '是否成功': '成功' if result.get('is_success', False) else '失败',
                    '响应时间(ms)': result.get('response_time', 0),
                    '提取实体': result.get('extracted_entities', ''),
                    '错误信息': result.get('error_message', '')
                }
                export_data.append(row)
            
            # 创建DataFrame
            df = pd.DataFrame(export_data)
            
            # 导出为Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='测试结果', index=False)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"导出测试结果失败: {e}")
            raise

# 全局文件处理器实例
_file_processor = None

def get_test_file_processor() -> TestFileProcessor:
    """获取测试文件处理器实例（单例模式）"""
    global _file_processor
    if _file_processor is None:
        _file_processor = TestFileProcessor()
    return _file_processor 