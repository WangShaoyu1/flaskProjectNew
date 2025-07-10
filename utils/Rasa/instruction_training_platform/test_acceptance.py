#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能对话训练平台 - 测试验收脚本
全面测试Excel解析、版本管理、YML生成等功能
"""

import requests
import json
import time
import os
from pathlib import Path
from datetime import datetime

class AcceptanceTest:
    """测试验收类"""
    
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.test_results = []
        self.library_id = None
        self.version_name = None
        
    def log_test(self, test_name, success, message="", details=None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   详细信息: {details}")
    
    def test_1_basic_health_check(self):
        """测试1: 基础健康检查"""
        print("\n=== 测试1: 基础健康检查 ===")
        
        try:
            # 检查根路径
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("根路径访问", True, f"系统状态: {data.get('data', {}).get('status', 'unknown')}")
            else:
                self.log_test("根路径访问", False, f"状态码: {response.status_code}")
                return False
            
            # 检查健康检查接口
            response = requests.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("健康检查接口", True, f"服务状态: {data.get('data', {}).get('status', 'unknown')}")
            else:
                self.log_test("健康检查接口", False, f"状态码: {response.status_code}")
                return False
            
            # 检查版本信息
            response = requests.get(f"{self.base_url}/api/version")
            if response.status_code == 200:
                data = response.json()
                version = data.get('data', {}).get('api_version', 'unknown')
                self.log_test("版本信息接口", True, f"API版本: {version}")
            else:
                self.log_test("版本信息接口", False, f"状态码: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("基础健康检查", False, f"连接失败: {str(e)}")
            return False
    
    def test_2_library_management(self):
        """测试2: 指令库管理"""
        print("\n=== 测试2: 指令库管理 ===")
        
        try:
            # 获取指令库列表
            response = requests.get(f"{self.base_url}/api/v2/libraries/list")
            if response.status_code == 200:
                data = response.json()
                libraries = data.get('data', {}).get('libraries', [])
                self.log_test("获取指令库列表", True, f"共有 {len(libraries)} 个指令库")
                
                # 如果有指令库，使用第一个；否则创建一个测试指令库
                if libraries:
                    self.library_id = libraries[0]['id']
                    self.log_test("使用现有指令库", True, f"指令库ID: {self.library_id}")
                else:
                    # 创建测试指令库
                    create_data = {
                        "name": "测试指令库",
                        "description": "用于验收测试的指令库",
                        "version": "1.0.0"
                    }
                    response = requests.post(f"{self.base_url}/api/v2/libraries/create", json=create_data)
                    if response.status_code == 200:
                        data = response.json()
                        self.library_id = data.get('data', {}).get('id')
                        self.log_test("创建测试指令库", True, f"指令库ID: {self.library_id}")
                    else:
                        self.log_test("创建测试指令库", False, f"状态码: {response.status_code}")
                        return False
            else:
                self.log_test("获取指令库列表", False, f"状态码: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("指令库管理测试", False, f"错误: {str(e)}")
            return False
    
    def test_3_excel_file_processing(self):
        """测试3: Excel文件处理"""
        print("\n=== 测试3: Excel文件处理 ===")
        
        try:
            # 检查测试Excel文件是否存在
            instruction_file = "public/402/双屏指令-20250616导出.xlsx"
            slot_file = "public/402/双屏词槽-20250616导出.xlsx"
            
            if not os.path.exists(instruction_file):
                self.log_test("检查指令Excel文件", False, f"文件不存在: {instruction_file}")
                return False
            
            if not os.path.exists(slot_file):
                self.log_test("检查词槽Excel文件", False, f"文件不存在: {slot_file}")
                return False
            
            self.log_test("检查Excel测试文件", True, "测试文件存在")
            
            # 测试Excel文件上传和处理
            with open(instruction_file, 'rb') as f1, open(slot_file, 'rb') as f2:
                files = {
                    'instruction_file': ('instruction.xlsx', f1, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    'slot_file': ('slot.xlsx', f2, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                }
                data = {
                    'library_id': str(self.library_id),
                    'description': '验收测试版本'
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v2/library-version/create-from-excel",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.version_name = result.get('data', {}).get('version_name')
                    file_count = result.get('data', {}).get('file_count', 0)
                    report = result.get('data', {}).get('conversion_report', {})
                    
                    self.log_test("Excel文件上传处理", True, 
                                f"版本: {self.version_name}, 生成文件: {file_count}个",
                                details=report.get('statistics'))
                else:
                    error_msg = response.text
                    self.log_test("Excel文件上传处理", False, 
                                f"状态码: {response.status_code}",
                                details=error_msg)
                    return False
            
            return True
            
        except Exception as e:
            self.log_test("Excel文件处理测试", False, f"错误: {str(e)}")
            return False
    
    def test_4_version_management(self):
        """测试4: 版本管理系统"""
        print("\n=== 测试4: 版本管理系统 ===")
        
        try:
            # 获取指令库版本列表
            response = requests.get(f"{self.base_url}/api/v2/library-version/list/{self.library_id}")
            if response.status_code == 200:
                data = response.json()
                versions = data.get('data', {}).get('versions', [])
                self.log_test("获取版本列表", True, f"共有 {len(versions)} 个版本")
                
                # 检查我们创建的版本是否在列表中
                version_found = any(v['version_name'] == self.version_name for v in versions)
                self.log_test("验证版本存在", version_found, 
                            f"版本 {self.version_name} {'存在' if version_found else '不存在'}")
            else:
                self.log_test("获取版本列表", False, f"状态码: {response.status_code}")
                return False
            
            # 获取版本文件内容
            response = requests.get(f"{self.base_url}/api/v2/library-version/files/{self.library_id}/{self.version_name}")
            if response.status_code == 200:
                data = response.json()
                files = data.get('data', {}).get('files', {})
                file_count = len(files)
                self.log_test("获取版本文件", True, f"版本包含 {file_count} 个文件")
                
                # 检查必要的RASA文件
                required_files = ['nlu.yml', 'domain.yml', 'rules.yml', 'stories.yml']
                missing_files = [f for f in required_files if f not in files]
                
                if not missing_files:
                    self.log_test("RASA文件完整性", True, "所有必要的RASA文件都存在")
                else:
                    self.log_test("RASA文件完整性", False, f"缺少文件: {missing_files}")
            else:
                self.log_test("获取版本文件", False, f"状态码: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("版本管理测试", False, f"错误: {str(e)}")
            return False
    
    def test_5_version_activation(self):
        """测试5: 版本激活功能"""
        print("\n=== 测试5: 版本激活功能 ===")
        
        try:
            # 激活版本到工作区
            response = requests.post(f"{self.base_url}/api/v2/library-version/activate/{self.library_id}/{self.version_name}")
            if response.status_code == 200:
                data = response.json()
                workspace_path = data.get('data', {}).get('workspace_path')
                self.log_test("版本激活", True, f"版本已激活到: {workspace_path}")
            else:
                self.log_test("版本激活", False, f"状态码: {response.status_code}")
                return False
            
            # 检查工作区文件是否存在
            workspace_files = [
                "rasa/data/domain.yml",
                "rasa/data/nlu.yml", 
                "rasa/data/rules.yml",
                "rasa/data/stories.yml"
            ]
            
            existing_files = []
            for file_path in workspace_files:
                if os.path.exists(file_path):
                    existing_files.append(file_path)
            
            if len(existing_files) == len(workspace_files):
                self.log_test("工作区文件检查", True, f"所有 {len(existing_files)} 个文件都存在")
            else:
                self.log_test("工作区文件检查", False, 
                            f"只有 {len(existing_files)}/{len(workspace_files)} 个文件存在")
            
            return True
            
        except Exception as e:
            self.log_test("版本激活测试", False, f"错误: {str(e)}")
            return False
    
    def test_6_api_completeness(self):
        """测试6: API接口完整性"""
        print("\n=== 测试6: API接口完整性 ===")
        
        try:
            # 测试版本索引接口
            response = requests.get(f"{self.base_url}/api/v2/library-version/index")
            if response.status_code == 200:
                data = response.json()
                library_count = data.get('data', {}).get('library_count', 0)
                self.log_test("版本索引接口", True, f"索引包含 {library_count} 个指令库")
            else:
                self.log_test("版本索引接口", False, f"状态码: {response.status_code}")
            
            # 测试手动创建版本接口
            manual_data = {
                'description': '手动创建的测试版本'
            }
            response = requests.post(
                f"{self.base_url}/api/v2/library-version/create-manual/{self.library_id}",
                data=manual_data
            )
            if response.status_code == 200:
                data = response.json()
                manual_version = data.get('data', {}).get('version_name')
                self.log_test("手动创建版本", True, f"创建版本: {manual_version}")
            else:
                self.log_test("手动创建版本", False, f"状态码: {response.status_code}")
            
            # 测试文档接口
            response = requests.get(f"{self.base_url}/docs")
            if response.status_code == 200:
                self.log_test("API文档访问", True, "Swagger文档可正常访问")
            else:
                self.log_test("API文档访问", False, f"状态码: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("API完整性测试", False, f"错误: {str(e)}")
            return False
    
    def test_7_file_content_validation(self):
        """测试7: 文件内容验证"""
        print("\n=== 测试7: 文件内容验证 ===")
        
        try:
            # 读取生成的RASA文件并验证内容
            rasa_files = {
                "rasa/data/domain.yml": "domain配置",
                "rasa/data/nlu.yml": "NLU训练数据",
                "rasa/data/rules.yml": "对话规则",
                "rasa/data/stories.yml": "对话故事"
            }
            
            for file_path, description in rasa_files.items():
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 基本内容验证
                    if len(content) > 100:  # 文件不能太小
                        if file_path.endswith('domain.yml'):
                            # domain.yml应该包含version、intents、entities等
                            required_keys = ['version', 'intents', 'entities', 'slots']
                            has_keys = all(key in content for key in required_keys)
                            self.log_test(f"{description}内容验证", has_keys, 
                                        f"包含必要字段: {has_keys}")
                        elif file_path.endswith('nlu.yml'):
                            # nlu.yml应该包含version、nlu等
                            has_nlu_data = 'version' in content and 'nlu:' in content
                            self.log_test(f"{description}内容验证", has_nlu_data,
                                        f"包含NLU数据: {has_nlu_data}")
                        else:
                            self.log_test(f"{description}内容验证", True, 
                                        f"文件大小: {len(content)} 字符")
                    else:
                        self.log_test(f"{description}内容验证", False, 
                                    f"文件内容过少: {len(content)} 字符")
                else:
                    self.log_test(f"{description}文件存在", False, f"文件不存在: {file_path}")
            
            return True
            
        except Exception as e:
            self.log_test("文件内容验证", False, f"错误: {str(e)}")
            return False
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 测试验收报告")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"📈 总测试数: {total_tests}")
        print(f"✅ 通过数: {passed_tests}")
        print(f"❌ 失败数: {failed_tests}")
        print(f"📊 通过率: {passed_tests/total_tests*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ 失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        # 保存详细报告
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'pass_rate': passed_tests/total_tests*100
                },
                'test_results': self.test_results,
                'library_id': self.library_id,
                'version_name': self.version_name
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return passed_tests == total_tests
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始智能对话训练平台验收测试")
        print("="*60)
        
        # 等待服务启动
        print("⏳ 等待服务启动...")
        time.sleep(3)
        
        test_methods = [
            self.test_1_basic_health_check,
            self.test_2_library_management,
            self.test_3_excel_file_processing,
            self.test_4_version_management,
            self.test_5_version_activation,
            self.test_6_api_completeness,
            self.test_7_file_content_validation
        ]
        
        for test_method in test_methods:
            try:
                success = test_method()
                if not success:
                    print(f"⚠️  测试 {test_method.__name__} 失败，继续后续测试...")
            except Exception as e:
                print(f"❌ 测试 {test_method.__name__} 异常: {str(e)}")
        
        return self.generate_report()


if __name__ == "__main__":
    # 运行验收测试
    tester = AcceptanceTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 所有测试通过！系统验收成功！")
        exit(0)
    else:
        print("\n⚠️  部分测试失败，请检查问题后重新测试")
        exit(1) 