import csv
import json
import yaml
import pandas as pd
from io import StringIO
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from services.database_service import IntentService, UtteranceService, ResponseService
from models.schemas import IntentCreate, UtteranceCreate, ResponseCreate, DataUploadResponse


class DataImportService:
    """数据导入服务"""

    @staticmethod
    def import_csv_data(db: Session, csv_content: str) -> DataUploadResponse:
        """
        导入 CSV 格式数据
        
        CSV 格式示例:
        intent_name,utterance_text,response_type,response_text,description
        greet,你好,success,您好！有什么可以帮您的？,问候意图
        greet,早上好,success,您好！有什么可以帮您的？,
        """
        try:
            errors = []
            imported_intents = 0
            imported_utterances = 0
            imported_responses = 0

            # 解析 CSV
            csv_reader = csv.DictReader(StringIO(csv_content))

            # 按意图分组处理数据
            intent_data = {}

            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    intent_name = row.get('intent_name', '').strip()
                    utterance_text = row.get('utterance_text', '').strip()
                    response_type = row.get('response_type', 'success').strip()
                    response_text = row.get('response_text', '').strip()
                    description = row.get('description', '').strip()

                    if not intent_name:
                        errors.append(f"第 {row_num} 行: 意图名称不能为空")
                        continue

                    if intent_name not in intent_data:
                        intent_data[intent_name] = {
                            'description': description,
                            'utterances': [],
                            'responses': []
                        }

                    if utterance_text:
                        intent_data[intent_name]['utterances'].append(utterance_text)

                    if response_text:
                        intent_data[intent_name]['responses'].append({
                            'type': response_type,
                            'text': response_text
                        })

                except Exception as e:
                    errors.append(f"第 {row_num} 行解析错误: {str(e)}")

            # 导入数据到数据库
            for intent_name, data in intent_data.items():
                try:
                    # 检查意图是否已存在
                    existing_intent = IntentService.get_intent_by_name(db, intent_name)

                    if not existing_intent:
                        # 创建新意图
                        intent_create = IntentCreate(
                            intent_name=intent_name,
                            description=data['description']
                        )
                        intent = IntentService.create_intent(db, intent_create)
                        imported_intents += 1
                    else:
                        intent = existing_intent

                    # 导入相似问
                    for utterance_text in data['utterances']:
                        utterance_create = UtteranceCreate(
                            intent_id=intent.id,
                            text=utterance_text
                        )
                        UtteranceService.create_utterance(db, utterance_create)
                        imported_utterances += 1

                    # 导入话术
                    for response_data in data['responses']:
                        response_create = ResponseCreate(
                            intent_id=intent.id,
                            type=response_data['type'],
                            text=response_data['text']
                        )
                        ResponseService.create_response(db, response_create)
                        imported_responses += 1

                except Exception as e:
                    errors.append(f"导入意图 '{intent_name}' 时出错: {str(e)}")

            return DataUploadResponse(
                message="CSV 数据导入完成",
                imported_intents=imported_intents,
                imported_utterances=imported_utterances,
                imported_responses=imported_responses,
                errors=errors
            )

        except Exception as e:
            return DataUploadResponse(
                message=f"CSV 数据导入失败: {str(e)}",
                imported_intents=0,
                imported_utterances=0,
                imported_responses=0,
                errors=[str(e)]
            )

    @staticmethod
    def import_yaml_data(db: Session, yaml_content: str) -> DataUploadResponse:
        """
        导入 YAML 格式数据 (Rasa NLU 格式)
        """
        try:
            errors = []
            imported_intents = 0
            imported_utterances = 0
            imported_responses = 0

            # 解析 YAML
            data = yaml.safe_load(yaml_content)

            if 'nlu' in data:
                # 处理 NLU 数据
                for item in data['nlu']:
                    if 'intent' in item:
                        intent_name = item['intent']
                        examples = item.get('examples', '')

                        try:
                            # 检查意图是否已存在
                            existing_intent = IntentService.get_intent_by_name(db, intent_name)

                            if not existing_intent:
                                intent_create = IntentCreate(intent_name=intent_name)
                                intent = IntentService.create_intent(db, intent_create)
                                imported_intents += 1
                            else:
                                intent = existing_intent

                            # 解析示例
                            if examples:
                                example_lines = examples.strip().split('\\n')
                                for line in example_lines:
                                    line = line.strip()
                                    if line.startswith('- '):
                                        utterance_text = line[2:].strip()
                                        if utterance_text:
                                            utterance_create = UtteranceCreate(
                                                intent_id=intent.id,
                                                text=utterance_text
                                            )
                                            UtteranceService.create_utterance(db, utterance_create)
                                            imported_utterances += 1

                        except Exception as e:
                            errors.append(f"处理意图 '{intent_name}' 时出错: {str(e)}")

            # 处理 Domain 数据中的响应
            if 'responses' in data:
                for response_key, response_list in data['responses'].items():
                    if response_key.startswith('utter_'):
                        intent_name = response_key[6:]  # 移除 'utter_' 前缀

                        try:
                            intent = IntentService.get_intent_by_name(db, intent_name)
                            if intent:
                                for response_item in response_list:
                                    if isinstance(response_item, dict) and 'text' in response_item:
                                        response_create = ResponseCreate(
                                            intent_id=intent.id,
                                            type='success',
                                            text=response_item['text']
                                        )
                                        ResponseService.create_response(db, response_create)
                                        imported_responses += 1

                        except Exception as e:
                            errors.append(f"处理响应 '{response_key}' 时出错: {str(e)}")

            return DataUploadResponse(
                message="YAML 数据导入完成",
                imported_intents=imported_intents,
                imported_utterances=imported_utterances,
                imported_responses=imported_responses,
                errors=errors
            )

        except Exception as e:
            return DataUploadResponse(
                message=f"YAML 数据导入失败: {str(e)}",
                imported_intents=0,
                imported_utterances=0,
                imported_responses=0,
                errors=[str(e)]
            )

    @staticmethod
    def import_json_data(db: Session, json_content: str) -> DataUploadResponse:
        """
        导入 JSON 格式数据
        
        JSON 格式示例:
        {
            "intents": [
                {
                    "intent_name": "greet",
                    "description": "问候意图",
                    "utterances": ["你好", "早上好"],
                    "responses": [
                        {"type": "success", "text": "您好！有什么可以帮您的？"}
                    ]
                }
            ]
        }
        """
        try:
            errors = []
            imported_intents = 0
            imported_utterances = 0
            imported_responses = 0

            # 解析 JSON
            data = json.loads(json_content)

            if 'intents' in data:
                for intent_data in data['intents']:
                    try:
                        intent_name = intent_data.get('intent_name')
                        description = intent_data.get('description', '')
                        utterances = intent_data.get('utterances', [])
                        responses = intent_data.get('responses', [])

                        if not intent_name:
                            errors.append("意图名称不能为空")
                            continue

                        # 检查意图是否已存在
                        existing_intent = IntentService.get_intent_by_name(db, intent_name)

                        if not existing_intent:
                            intent_create = IntentCreate(
                                intent_name=intent_name,
                                description=description
                            )
                            intent = IntentService.create_intent(db, intent_create)
                            imported_intents += 1
                        else:
                            intent = existing_intent

                        # 导入相似问
                        for utterance_text in utterances:
                            if utterance_text.strip():
                                utterance_create = UtteranceCreate(
                                    intent_id=intent.id,
                                    text=utterance_text.strip()
                                )
                                UtteranceService.create_utterance(db, utterance_create)
                                imported_utterances += 1

                        # 导入话术
                        for response_data in responses:
                            if isinstance(response_data, dict):
                                response_create = ResponseCreate(
                                    intent_id=intent.id,
                                    type=response_data.get('type', 'success'),
                                    text=response_data.get('text', '')
                                )
                                ResponseService.create_response(db, response_create)
                                imported_responses += 1

                    except Exception as e:
                        errors.append(f"处理意图数据时出错: {str(e)}")

            return DataUploadResponse(
                message="JSON 数据导入完成",
                imported_intents=imported_intents,
                imported_utterances=imported_utterances,
                imported_responses=imported_responses,
                errors=errors
            )

        except Exception as e:
            return DataUploadResponse(
                message=f"JSON 数据导入失败: {str(e)}",
                imported_intents=0,
                imported_utterances=0,
                imported_responses=0,
                errors=[str(e)]
            )


class DataExportService:
    """数据导出服务"""

    @staticmethod
    def export_to_rasa_format(db: Session) -> Dict[str, str]:
        """
        导出为 Rasa 格式的训练数据
        
        Returns:
            Dict: {"nlu_data": "...", "domain_data": "..."}
        """
        from services.rasa_service import RasaService

        rasa_service = RasaService()
        nlu_data, domain_data = rasa_service.generate_training_data(db)

        return {
            "nlu_data": nlu_data,
            "domain_data": domain_data
        }

    @staticmethod
    def export_to_csv(db: Session) -> str:
        """
        导出为 CSV 格式
        """
        intents = IntentService.get_intents(db)

        csv_data = []
        csv_data.append(['intent_name', 'utterance_text', 'response_type', 'response_text', 'description'])

        for intent in intents:
            utterances = UtteranceService.get_utterances_by_intent(db, intent.id)
            responses = ResponseService.get_responses_by_intent(db, intent.id)

            # 如果没有相似问和话术，至少导出意图信息
            if not utterances and not responses:
                csv_data.append([intent.intent_name, '', '', '', intent.description or ''])

            # 导出相似问
            for utterance in utterances:
                csv_data.append([intent.intent_name, utterance.text, '', '', intent.description or ''])

            # 导出话术
            for response in responses:
                csv_data.append([intent.intent_name, '', response.type, response.text, intent.description or ''])

        # 转换为 CSV 字符串
        output = StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_data)
        return output.getvalue()
