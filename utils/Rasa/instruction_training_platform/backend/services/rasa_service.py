"""
RASA服务类
用于加载和使用训练好的模型进行意图识别和实体提取
"""

import os
import json
import logging
import requests
import subprocess
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """预测结果数据类"""
    intent: str
    confidence: float
    entities: List[Dict[str, Any]]
    response_time: float = 0.0
    
    def to_dict(self):
        return {
            'intent': self.intent,
            'confidence': self.confidence,
            'entities': self.entities,
            'response_time': self.response_time
        }

class RasaService:
    """RASA服务类"""
    
    def __init__(self, rasa_project_path: str = None):
        self.rasa_project_path = rasa_project_path or os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'rasa')
        self.rasa_server_url = "http://localhost:5005"
        self.current_model_path = None
        self.server_process = None
        self.is_server_running = False
        
    def check_rasa_status(self) -> bool:
        """检查RASA服务状态"""
        try:
            response = requests.get(f"{self.rasa_server_url}/status", timeout=5)
            self.is_server_running = response.status_code == 200
            return self.is_server_running
        except Exception as e:
            logger.warning(f"RASA服务状态检查失败: {e}")
            self.is_server_running = False
            return False
    
    def get_latest_model_path(self) -> Optional[str]:
        """获取最新的模型路径"""
        models_dir = os.path.join(self.rasa_project_path, 'models')
        if not os.path.exists(models_dir):
            return None
            
        model_files = [f for f in os.listdir(models_dir) if f.endswith('.tar.gz')]
        if not model_files:
            return None
            
        # 按修改时间排序，获取最新的模型
        model_files.sort(key=lambda x: os.path.getmtime(os.path.join(models_dir, x)), reverse=True)
        return os.path.join(models_dir, model_files[0])
    
    def get_model_path_by_version(self, version_id: str) -> Optional[str]:
        """根据版本ID获取模型路径"""
        models_dir = os.path.join(self.rasa_project_path, 'models')
        if not os.path.exists(models_dir):
            return None
            
        # 查找包含版本ID的模型文件
        for filename in os.listdir(models_dir):
            if filename.endswith('.tar.gz') and version_id in filename:
                return os.path.join(models_dir, filename)
        
        # 如果没有找到特定版本，返回最新模型
        return self.get_latest_model_path()
    
    def start_rasa_server(self, model_path: str = None) -> bool:
        """启动RASA服务器"""
        try:
            # 检查是否已经在运行
            if self.check_rasa_status():
                logger.info("RASA服务器已在运行")
                return True
            
            # 确定模型路径
            if not model_path:
                model_path = self.get_latest_model_path()
                
            if not model_path or not os.path.exists(model_path):
                logger.error(f"模型文件不存在: {model_path}")
                return False
            
            # 启动RASA服务器
            cmd = [
                'rasa', 'run',
                '--model', model_path,
                '--endpoints', os.path.join(self.rasa_project_path, 'endpoints.yml'),
                '--port', '5005',
                '--enable-api'
            ]
            
            logger.info(f"启动RASA服务器: {' '.join(cmd)}")
            self.server_process = subprocess.Popen(
                cmd,
                cwd=self.rasa_project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待服务器启动
            max_wait = 30  # 最多等待30秒
            wait_time = 0
            while wait_time < max_wait:
                if self.check_rasa_status():
                    logger.info("RASA服务器启动成功")
                    self.current_model_path = model_path
                    return True
                time.sleep(1)
                wait_time += 1
            
            logger.error("RASA服务器启动超时")
            return False
            
        except Exception as e:
            logger.error(f"启动RASA服务器失败: {e}")
            return False
    
    def stop_rasa_server(self):
        """停止RASA服务器"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
            self.is_server_running = False
            logger.info("RASA服务器已停止")
    
    def predict_intent(self, text: str, model_version_id: str = None) -> PredictionResult:
        """预测意图"""
        start_time = time.time()
        
        try:
            # 检查服务状态
            if not self.check_rasa_status():
                # 尝试启动服务器
                model_path = None
                if model_version_id:
                    model_path = self.get_model_path_by_version(model_version_id)
                
                if not self.start_rasa_server(model_path):
                    raise Exception("RASA服务器启动失败")
            
            # 发送预测请求
            payload = {"text": text}
            response = requests.post(
                f"{self.rasa_server_url}/model/parse",
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"预测请求失败: {response.status_code}")
            
            result = response.json()
            
            # 解析结果
            intent_data = result.get('intent', {})
            intent_name = intent_data.get('name', 'nlu_fallback')
            confidence = intent_data.get('confidence', 0.0)
            entities = result.get('entities', [])
            
            # 计算响应时间
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            return PredictionResult(
                intent=intent_name,
                confidence=confidence,
                entities=entities,
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"意图预测失败: {e}")
            response_time = (time.time() - start_time) * 1000
            
            # 返回失败结果
            return PredictionResult(
                intent='nlu_fallback',
                confidence=0.0,
                entities=[],
                response_time=response_time
            )
    
    def batch_predict(self, texts: List[str], model_version_id: str = None) -> List[PredictionResult]:
        """批量预测"""
        results = []
        
        # 确保服务器运行
        if not self.check_rasa_status():
            model_path = None
            if model_version_id:
                model_path = self.get_model_path_by_version(model_version_id)
            
            if not self.start_rasa_server(model_path):
                # 如果服务器启动失败，返回失败结果
                return [PredictionResult(
                    intent='nlu_fallback',
                    confidence=0.0,
                    entities=[],
                    response_time=0.0
                ) for _ in texts]
        
        # 逐个预测
        for text in texts:
            result = self.predict_intent(text, model_version_id)
            results.append(result)
        
        return results
    
    def get_model_info(self, model_path: str = None) -> Dict[str, Any]:
        """获取模型信息"""
        try:
            if not model_path:
                model_path = self.current_model_path or self.get_latest_model_path()
            
            if not model_path or not os.path.exists(model_path):
                return {}
            
            # 获取模型文件信息
            model_info = {
                'model_path': model_path,
                'model_size': os.path.getsize(model_path),
                'created_time': os.path.getctime(model_path),
                'modified_time': os.path.getmtime(model_path)
            }
            
            return model_info
            
        except Exception as e:
            logger.error(f"获取模型信息失败: {e}")
            return {}
    
    def validate_model(self, model_path: str) -> bool:
        """验证模型文件"""
        try:
            if not os.path.exists(model_path):
                return False
            
            # 检查文件大小
            if os.path.getsize(model_path) < 1024:  # 至少1KB
                return False
            
            # 检查文件格式
            if not model_path.endswith('.tar.gz'):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"模型验证失败: {e}")
            return False
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取可用的模型列表"""
        models = []
        models_dir = os.path.join(self.rasa_project_path, 'models')
        
        if not os.path.exists(models_dir):
            return models
        
        for filename in os.listdir(models_dir):
            if filename.endswith('.tar.gz'):
                model_path = os.path.join(models_dir, filename)
                if self.validate_model(model_path):
                    models.append({
                        'filename': filename,
                        'path': model_path,
                        'size': os.path.getsize(model_path),
                        'created_time': os.path.getctime(model_path),
                        'modified_time': os.path.getmtime(model_path)
                    })
        
        # 按修改时间排序
        models.sort(key=lambda x: x['modified_time'], reverse=True)
        return models

# 全局RASA服务实例
_rasa_service = None

def get_rasa_service() -> RasaService:
    """获取RASA服务实例（单例模式）"""
    global _rasa_service
    if _rasa_service is None:
        _rasa_service = RasaService()
    return _rasa_service

def cleanup_rasa_service():
    """清理RASA服务"""
    global _rasa_service
    if _rasa_service:
        _rasa_service.stop_rasa_server()
        _rasa_service = None 