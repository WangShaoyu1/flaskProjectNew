#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Slot识别测试工具

测试Rasa NLU对包含slot的中文句子的识别能力
验证映射系统是否正常工作
"""

import requests
import json
import sys

def test_nlu_slot_recognition():
    """测试NLU slot识别功能"""
    
    # 测试用例：包含不同slot的中文句子
    test_cases = [
        {
            'text': '设置大份量',
            'expected_entity': '份量',
            'expected_value': '大份'
        },
        {
            'text': '调成中火',
            'expected_entity': '火力', 
            'expected_value': '中火'
        },
        {
            'text': '选择脆嫩口感',
            'expected_entity': '口感',
            'expected_value': '脆嫩'
        },
        {
            'text': '播报模式改为简易模式',
            'expected_entity': '播报模式',
            'expected_value': '简易模式'
        },
        {
            'text': '选择第三个',
            'expected_entity': '第N',
            'expected_value': '第三'
        }
    ]
    
    print('🧪 测试Rasa NLU Slot识别')
    print('=' * 60)
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        print(f'\\n[{i}/{total_count}] 测试用例: {case["text"]}')
        print('-' * 40)
        
        try:
            # 发送请求到Rasa NLU
            response = requests.post(
                'http://localhost:5005/model/parse',
                json={'text': case['text']},
                timeout=10
            )
            
            if response.status_code != 200:
                print(f'❌ HTTP错误: {response.status_code}')
                continue
                
            result = response.json()
            
            # 显示识别结果
            intent = result.get('intent', {})
            print(f'🎯 意图: {intent.get("name", "未识别")}')
            print(f'📊 置信度: {intent.get("confidence", 0):.3f}')
            
            # 检查实体识别
            entities = result.get('entities', [])
            if entities:
                print('🏷️  实体识别:')
                entity_found = False
                
                for entity in entities:
                    entity_name = entity.get('entity', '')
                    entity_value = entity.get('value', '')
                    
                    print(f'   - {entity_name}: {entity_value}')
                    
                    # 检查是否匹配预期
                    if (entity_name == case['expected_entity'] and 
                        entity_value == case['expected_value']):
                        entity_found = True
                
                if entity_found:
                    print('✅ 实体识别正确')
                    success_count += 1
                else:
                    print(f'❌ 实体识别错误，预期: {case["expected_entity"]} = {case["expected_value"]}')
            else:
                print('🏷️  实体识别: 无')
                print(f'❌ 未识别到预期实体: {case["expected_entity"]} = {case["expected_value"]}')
                
        except requests.exceptions.RequestException as e:
            print(f'❌ 网络请求失败: {e}')
        except Exception as e:
            print(f'❌ 测试失败: {e}')
    
    # 显示测试总结
    print('\\n' + '=' * 60)
    print('📋 测试总结')
    print(f'✅ 成功: {success_count}/{total_count}')
    print(f'❌ 失败: {total_count - success_count}/{total_count}')
    print(f'📊 成功率: {success_count/total_count*100:.1f}%')
    
    if success_count == total_count:
        print('\\n🎉 所有测试通过！Slot映射系统工作正常！')
        return True
    else:
        print('\\n⚠️  部分测试失败，请检查Rasa服务和训练数据')
        return False

def check_rasa_service():
    """检查Rasa服务状态"""
    try:
        response = requests.get('http://localhost:5005/status', timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f'✅ Rasa服务运行正常')
            print(f'📦 模型: {status.get("model_file", "未知")}')
            return True
        else:
            print(f'❌ Rasa服务响应异常: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ 无法连接到Rasa服务: {e}')
        print('💡 请确保Rasa服务正在运行 (http://localhost:5005)')
        return False

def main():
    """主函数"""
    print('🔍 Slot识别测试工具')
    print('=' * 60)
    
    # 检查Rasa服务状态
    print('\\n1. 检查Rasa服务状态...')
    if not check_rasa_service():
        return 1
    
    # 执行slot识别测试
    print('\\n2. 执行Slot识别测试...')
    success = test_nlu_slot_recognition()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 