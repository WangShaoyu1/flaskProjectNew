import requests
import os
import yaml
import json
import subprocess
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from services.database_service import IntentService, UtteranceService, ResponseService, ModelService, TrainingTaskService
from models.schemas import PredictResponse, TrainResponse, BatchTestResponse, TestResult
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RasaService:
    """Rasa 服务管理类"""
    
    def __init__(self, rasa_server_url: str = "http://localhost:5005", 
                 rasa_project_root: str = None):
        self.rasa_server_url = rasa_server_url
        self.rasa_project_root = rasa_project_root or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "rasa")
        )
        self.rasa_data_path = os.path.join(self.rasa_project_root, "data")
        self.rasa_models_path = os.path.join(self.rasa_project_root, "models")
        
        # 确保目录存在
        os.makedirs(self.rasa_data_path, exist_ok=True)
        os.makedirs(self.rasa_models_path, exist_ok=True)
    
    def predict_intent(self, text: str) -> PredictResponse:
        """
        调用 Rasa 进行意图预测
        
        Args:
            text: 用户输入文本
            
        Returns:
            PredictResponse: 预测结果
        """
        try:
            rasa_parse_url = f"{self.rasa_server_url}/model/parse"
            response = requests.post(
                rasa_parse_url, 
                json={"text": text},
                timeout=10
            )
            response.raise_for_status()
            
            rasa_result = response.json()
            
            # 提取核心信息
            intent_info = rasa_result.get("intent", {})
            intent_name = intent_info.get("name")
            confidence = intent_info.get("confidence", 0.0)
            entities = rasa_result.get("entities", [])
            
            return PredictResponse(
                text=text,
                intent=intent_name,
                confidence=confidence,
                entities=entities,
                raw_rasa_response=rasa_result
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Rasa 服务连接错误: {e}")
            raise Exception(f"无法连接到 Rasa 服务: {e}")
        except Exception as e:
            logger.error(f"意图预测错误: {e}")
            raise Exception(f"意图预测失败: {e}")
    
    def generate_training_data(self, db: Session) -> tuple[str, str]:
        """
        从数据库生成 Rasa 训练数据
        
        Args:
            db: 数据库会话
            
        Returns:
            tuple: (nlu_data, domain_data) YAML 格式字符串
        """
        try:
            # 获取所有意图和相关数据
            intents = IntentService.get_intents(db)
            
            # 生成 NLU 数据
            nlu_data = {
                "version": "3.1",
                "nlu": []
            }
            
            # 生成 Domain 数据
            domain_data = {
                "version": "3.1",
                "intents": [],
                "entities": [],
                "responses": {},
                "session_config": {
                    "session_expiration_time": 60,
                    "carry_over_slots_to_new_session": True
                }
            }
            
            entities_set = set()
            
            for intent in intents:
                intent_name = intent.intent_name
                domain_data["intents"].append(intent_name)
                
                # 获取相似问
                utterances = UtteranceService.get_utterances_by_intent(db, intent.id)
                if utterances:
                    intent_examples = {
                        "intent": intent_name,
                        "examples": ""
                    }
                    
                    examples_list = []
                    for utterance in utterances:
                        text = utterance.text
                        
                        # 处理实体标注
                        if utterance.entities:
                            try:
                                entities_info = json.loads(utterance.entities)
                                for entity in entities_info:
                                    entity_name = entity.get("entity")
                                    if entity_name:
                                        entities_set.add(entity_name)
                                        # 这里可以添加实体标注逻辑
                            except json.JSONDecodeError:
                                pass
                        
                        examples_list.append(f"- {text}")
                    
                    intent_examples["examples"] = "\\n".join(examples_list)
                    nlu_data["nlu"].append(intent_examples)
                
                # 获取话术
                responses = ResponseService.get_responses_by_intent(db, intent.id)
                if responses:
                    response_key = f"utter_{intent_name}"
                    response_texts = []
                    
                    for response in responses:
                        response_texts.append({"text": response.text})
                    
                    domain_data["responses"][response_key] = response_texts
            
            # 添加实体到 domain
            domain_data["entities"] = list(entities_set)
            
            # 添加默认的 fallback 响应
            if "utter_fallback" not in domain_data["responses"]:
                domain_data["responses"]["utter_fallback"] = [
                    {"text": "抱歉，我没有理解您的意思，请您再说一遍。"}
                ]
            
            # 转换为 YAML 字符串
            nlu_yaml = yaml.dump(nlu_data, allow_unicode=True, default_flow_style=False)
            domain_yaml = yaml.dump(domain_data, allow_unicode=True, default_flow_style=False)
            
            return nlu_yaml, domain_yaml
            
        except Exception as e:
            logger.error(f"生成训练数据错误: {e}")
            raise Exception(f"生成训练数据失败: {e}")
    
    def train_model(self, db: Session, nlu_data: str = None, domain_data: str = None) -> TrainResponse:
        """
        触发 Rasa 模型训练
        
        Args:
            db: 数据库会话
            nlu_data: NLU 数据 (可选，如果不提供则从数据库生成)
            domain_data: Domain 数据 (可选，如果不提供则从数据库生成)
            
        Returns:
            TrainResponse: 训练响应
        """
        try:
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 如果没有提供数据，从数据库生成
            if not nlu_data or not domain_data:
                nlu_data, domain_data = self.generate_training_data(db)
            
            # 写入训练数据文件
            nlu_file_path = os.path.join(self.rasa_data_path, "nlu.yml")
            domain_file_path = os.path.join(self.rasa_data_path, "domain.yml")
            
            with open(nlu_file_path, "w", encoding="utf-8") as f:
                f.write(nlu_data)
            
            with open(domain_file_path, "w", encoding="utf-8") as f:
                f.write(domain_data)
            
            logger.info(f"训练数据已写入: {nlu_file_path}, {domain_file_path}")
            
            # 创建训练任务记录
            from models.schemas import TrainingTaskCreate
            task = TrainingTaskCreate(
                task_id=task_id,
                status="pending"
            )
            TrainingTaskService.create_task(db, task)
            
            # 生成模型版本号
            model_version = f"model-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # 执行训练命令 (这里使用同步方式，实际项目中建议使用异步)
            command = ["rasa", "train", "--force", "--out", self.rasa_models_path]
            
            logger.info(f"开始执行 Rasa 训练命令: {' '.join(command)}")
            
            # 更新任务状态为运行中
            TrainingTaskService.update_task_status(db, task_id, "running", 0.1)
            
            try:
                result = subprocess.run(
                    command,
                    cwd=self.rasa_project_root,
                    capture_output=True,
                    text=True,
                    check=True,
                    encoding="utf-8"
                )
                
                logger.info("Rasa 训练完成")
                logger.info(f"STDOUT: {result.stdout}")
                
                # 获取最新模型文件
                model_files = [f for f in os.listdir(self.rasa_models_path) if f.endswith(".tar.gz")]
                if model_files:
                    latest_model = max(model_files, key=lambda f: os.path.getmtime(
                        os.path.join(self.rasa_models_path, f)
                    ))
                    model_file_path = os.path.join(self.rasa_models_path, latest_model)
                    
                    # 创建模型记录
                    from models.schemas import ModelCreate
                    model_data = ModelCreate(
                        version=model_version,
                        file_path=model_file_path,
                        status="success",
                        is_active=True
                    )
                    
                    # 创建模型记录
                    model_record = ModelService.create_model(db, model_data)
                    
                    # 设置为激活模型
                    ModelService.set_active_model(db, model_record.id)
                    
                    # 更新任务状态为完成
                    TrainingTaskService.update_task_status(
                        db, task_id, "completed", 1.0, result.stdout
                    )
                    
                    return TrainResponse(
                        message="模型训练成功",
                        task_id=task_id,
                        model_version=model_version
                    )
                else:
                    raise Exception("未找到训练生成的模型文件")
                    
            except subprocess.CalledProcessError as e:
                error_msg = f"Rasa 训练失败: {e.stderr}"
                logger.error(error_msg)
                
                # 更新任务状态为失败
                TrainingTaskService.update_task_status(
                    db, task_id, "failed", error_message=error_msg
                )
                
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"训练模型错误: {e}")
            raise Exception(f"训练模型失败: {e}")
    
    def batch_test(self, test_data: List[Dict[str, str]], 
                   model_version: str = None) -> BatchTestResponse:
        """
        批量测试模型性能
        
        Args:
            test_data: 测试数据列表 [{"text": "...", "expected_intent": "..."}]
            model_version: 模型版本 (可选)
            
        Returns:
            BatchTestResponse: 测试结果
        """
        try:
            results = []
            correct_count = 0
            
            for test_item in test_data:
                text = test_item.get("text", "")
                expected_intent = test_item.get("expected_intent", "")
                
                # 预测意图
                prediction = self.predict_intent(text)
                predicted_intent = prediction.intent
                confidence = prediction.confidence
                
                # 判断是否正确
                is_correct = predicted_intent == expected_intent
                if is_correct:
                    correct_count += 1
                
                results.append(TestResult(
                    text=text,
                    expected_intent=expected_intent,
                    predicted_intent=predicted_intent,
                    confidence=confidence,
                    is_correct=is_correct
                ))
            
            # 计算准确率
            total_tests = len(test_data)
            accuracy = correct_count / total_tests if total_tests > 0 else 0.0
            
            return BatchTestResponse(
                total_tests=total_tests,
                correct_predictions=correct_count,
                accuracy=accuracy,
                results=results
            )
            
        except Exception as e:
            logger.error(f"批量测试错误: {e}")
            raise Exception(f"批量测试失败: {e}")
    
    def check_rasa_status(self) -> bool:
        """
        检查 Rasa 服务状态
        
        Returns:
            bool: 服务是否可用
        """
        try:
            response = requests.get(f"{self.rasa_server_url}/status", timeout=5)
            return response.status_code == 200
        except:
            return False

