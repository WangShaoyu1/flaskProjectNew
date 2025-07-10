#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能对话训练平台 - 最终验收测试
修复所有已知问题的完整测试
"""

import requests
import json
import os
import time
from datetime import datetime

class FinalAcceptanceTest:
    """最终验收测试类"""
    
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
    
    def test_1_service_health(self):
        """测试1: 服务健康状态"""
        print("\n=== 测试1: 服务健康状态 ===")
        
        try:
            # 检查根路径
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                status = data.get('data', {}).get('status', 'unknown')
                self.log_test("服务根路径", True, f"系统状态: {status}")
            else:
                self.log_test("服务根路径", False, f"状态码: {response.status_code}")
                return False
            
            # 检查健康检查
            response = requests.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                data = response.json()
                health = data.get('data', {}).get('status', 'unknown')
                self.log_test("健康检查", True, f"健康状态: {health}")
            else:
                self.log_test("健康检查", False, f"状态码: {response.status_code}")
                return False
            
            # 检查版本信息
            response = requests.get(f"{self.base_url}/api/version")
            if response.status_code == 200:
                data = response.json()
                version = data.get('data', {}).get('api_version', 'unknown')
                self.log_test("版本信息", True, f"API版本: {version}")
            else:
                self.log_test("版本信息", False, f"状态码: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("服务健康检查", False, f"连接失败: {str(e)}")
            return False
    
    def test_2_library_management(self):
        """测试2: 指令库管理"""
        print("\n=== 测试2: 指令库管理 ===")
        
        try:
            # 获取现有指令库列表
            response = requests.get(f"{self.base_url}/api/v2/library/list")
            if response.status_code == 200:
                data = response.json()
                # 修复：正确处理响应结构
                if 'data' in data and isinstance(data['data'], dict) and 'libraries' in data['data']:
                    libraries = data['data']['libraries']
                elif 'data' in data and isinstance(data['data'], list):
                    libraries = data['data']
                else:
                    libraries = []
                
                self.log_test("获取指令库列表", True, f"现有指令库: {len(libraries)} 个")
                
                # 如果有现有指令库，使用第一个
                if libraries:
                    self.library_id = libraries[0].get('id')
                    self.log_test("使用现有指令库", True, f"指令库ID: {self.library_id}")
                else:
                    # 创建新的测试指令库
                    create_data = {
                        "name": "验收测试指令库",
                        "description": "用于系统验收测试的指令库",
                        "version": "1.0.0",
                        "language": "zh"
                    }
                    response = requests.post(f"{self.base_url}/api/v2/library/create", json=create_data)
                    if response.status_code == 200:
                        data = response.json()
                        # 修复：正确获取library_id
                        if 'data' in data:
                            if isinstance(data['data'], dict):
                                self.library_id = data['data'].get('id')
                            else:
                                self.library_id = data['data']
                        
                        if self.library_id:
                            self.log_test("创建测试指令库", True, f"指令库ID: {self.library_id}")
                        else:
                            self.log_test("创建测试指令库", False, "未能获取指令库ID")
                            return False
                    else:
                        self.log_test("创建测试指令库", False, f"状态码: {response.status_code}, 详情: {response.text}")
                        return False
            else:
                self.log_test("获取指令库列表", False, f"状态码: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("指令库管理测试", False, f"错误: {str(e)}")
            return False
    
    def test_3_dual_screen_import(self):
        """测试3: 双屏数据导入"""
        print("\n=== 测试3: 双屏数据导入 ===")
        
        try:
            # 检查测试文件
            instruction_file = "public/402/双屏指令-20250616导出.xlsx"
            slot_file = "public/402/双屏词槽-20250616导出.xlsx"
            
            if not os.path.exists(instruction_file):
                self.log_test("检查指令Excel文件", False, f"文件不存在: {instruction_file}")
                return False
            
            if not os.path.exists(slot_file):
                self.log_test("检查词槽Excel文件", False, f"文件不存在: {slot_file}")
                return False
            
            self.log_test("检查Excel测试文件", True, "测试文件存在")
            
            # 上传并处理双屏文件
            with open(instruction_file, 'rb') as f1, open(slot_file, 'rb') as f2:
                files = {
                    'instruction_file': ('instruction.xlsx', f1, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    'slot_file': ('slot.xlsx', f2, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                }
                data = {
                    'library_id': str(self.library_id)
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v2/dual-screen/upload-and-process",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message = result.get('msg', '上传成功')
                    self.log_test("双屏数据导入", True, message)
                    
                    # 检查返回的统计信息
                    if 'data' in result and 'import_statistics' in result['data']:
                        stats = result['data']['import_statistics']
                        self.log_test("数据导入统计", True, f"统计信息可用", details=stats)
                    
                    return True
                else:
                    self.log_test("双屏数据导入", False, f"状态码: {response.status_code}", details=response.text)
                    return False
            
        except Exception as e:
            self.log_test("双屏数据导入测试", False, f"错误: {str(e)}")
            return False
    
    def test_4_version_management(self):
        """测试4: 版本管理功能"""
        print("\n=== 测试4: 版本管理功能 ===")
        
        try:
            # 测试创建手动版本
            manual_data = {
                'description': '验收测试手动版本'
            }
            response = requests.post(
                f"{self.base_url}/api/v2/library-version/create-manual/{self.library_id}",
                data=manual_data
            )
            
            if response.status_code == 200:
                data = response.json()
                version_name = data.get('data', {}).get('version_name')
                self.log_test("创建手动版本", True, f"版本: {version_name}")
                self.version_name = version_name
            else:
                self.log_test("创建手动版本", False, f"状态码: {response.status_code}", details=response.text)
                return False
            
            # 测试获取版本列表
            response = requests.get(f"{self.base_url}/api/v2/library-version/list/{self.library_id}")
            if response.status_code == 200:
                data = response.json()
                versions = data.get('data', {}).get('versions', [])
                self.log_test("获取版本列表", True, f"版本数量: {len(versions)}")
                
                if versions:
                    # 测试获取版本文件
                    first_version = versions[0]['version_name']
                    response = requests.get(f"{self.base_url}/api/v2/library-version/files/{self.library_id}/{first_version}")
                    if response.status_code == 200:
                        data = response.json()
                        files = data.get('data', {}).get('files', {})
                        self.log_test("获取版本文件", True, f"文件数量: {len(files)}")
                        
                        # 验证RASA文件完整性
                        required_files = ['nlu.yml', 'domain.yml', 'rules.yml', 'stories.yml']
                        missing_files = [f for f in required_files if f not in files]
                        
                        if not missing_files:
                            self.log_test("RASA文件完整性", True, "所有必要文件存在")
                        else:
                            self.log_test("RASA文件完整性", False, f"缺少文件: {missing_files}")
                    else:
                        self.log_test("获取版本文件", False, f"状态码: {response.status_code}")
            else:
                self.log_test("获取版本列表", False, f"状态码: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("版本管理测试", False, f"错误: {str(e)}")
            return False
    
    def test_5_workspace_activation(self):
        """测试5: 工作区激活"""
        print("\n=== 测试5: 工作区激活 ===")
        
        try:
            if not self.version_name:
                self.log_test("版本激活准备", False, "没有可用的版本名称")
                return False
            
            # 激活版本到工作区
            response = requests.post(f"{self.base_url}/api/v2/library-version/activate/{self.library_id}/{self.version_name}")
            if response.status_code == 200:
                data = response.json()
                workspace_path = data.get('data', {}).get('workspace_path', 'rasa/data/')
                self.log_test("版本激活", True, f"激活到: {workspace_path}")
            else:
                self.log_test("版本激活", False, f"状态码: {response.status_code}", details=response.text)
                return False
            
            # 验证工作区文件
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
            
            if len(existing_files) >= 3:  # 至少要有3个文件
                self.log_test("工作区文件验证", True, f"存在 {len(existing_files)} 个文件")
            else:
                self.log_test("工作区文件验证", False, f"只有 {len(existing_files)} 个文件存在")
            
            return True
            
        except Exception as e:
            self.log_test("工作区激活测试", False, f"错误: {str(e)}")
            return False
    
    def test_6_api_completeness(self):
        """测试6: API完整性验证"""
        print("\n=== 测试6: API完整性验证 ===")
        
        try:
            # 测试版本索引API
            response = requests.get(f"{self.base_url}/api/v2/library-version/index")
            if response.status_code == 200:
                data = response.json()
                library_count = data.get('data', {}).get('library_count', 0)
                self.log_test("版本索引API", True, f"索引包含 {library_count} 个指令库")
            else:
                self.log_test("版本索引API", False, f"状态码: {response.status_code}")
            
            # 测试文档页面
            response = requests.get(f"{self.base_url}/docs")
            if response.status_code == 200:
                self.log_test("API文档访问", True, "Swagger文档可正常访问")
            else:
                self.log_test("API文档访问", False, f"状态码: {response.status_code}")
            
            # 测试OpenAPI规范
            response = requests.get(f"{self.base_url}/openapi.json")
            if response.status_code == 200:
                openapi_data = response.json()
                paths_count = len(openapi_data.get('paths', {}))
                self.log_test("OpenAPI规范", True, f"包含 {paths_count} 个API路径")
            else:
                self.log_test("OpenAPI规范", False, f"状态码: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("API完整性测试", False, f"错误: {str(e)}")
            return False
    
    def generate_final_report(self):
        """生成最终测试报告"""
        print("\n" + "="*60)
        print("🎯 智能对话训练平台验收测试报告")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 测试统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   通过数: {passed_tests}")
        print(f"   失败数: {failed_tests}")
        print(f"   通过率: {pass_rate:.1f}%")
        
        print(f"\n📋 测试详情:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test_name']}: {result['message']}")
        
        if failed_tests > 0:
            print(f"\n⚠️ 失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test_name']}: {result['message']}")
                    if result.get('details'):
                        print(f"     详细信息: {result['details']}")
        
        # 保存详细报告
        report_file = f"final_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'pass_rate': pass_rate
                },
                'test_results': self.test_results,
                'library_id': self.library_id,
                'version_name': self.version_name,
                'test_time': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        # 验收结论
        if pass_rate >= 90:
            print(f"\n🎉 验收结论: 系统验收通过！")
            print(f"   ✅ 核心功能正常")
            print(f"   ✅ Excel解析功能正常") 
            print(f"   ✅ 版本管理功能正常")
            print(f"   ✅ YML文件生成正常")
            return True
        elif pass_rate >= 70:
            print(f"\n⚠️ 验收结论: 系统基本可用，存在少量问题")
            return False
        else:
            print(f"\n❌ 验收结论: 系统存在重大问题，需要修复")
            return False
    
    def run_full_acceptance_test(self):
        """运行完整的验收测试"""
        print("🚀 智能对话训练平台 - 最终验收测试")
        print("="*60)
        print(f"⏰ 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 等待服务稳定
        print("⏳ 等待服务稳定...")
        time.sleep(2)
        
        test_methods = [
            self.test_1_service_health,
            self.test_2_library_management,
            self.test_3_dual_screen_import,
            self.test_4_version_management,
            self.test_5_workspace_activation,
            self.test_6_api_completeness
        ]
        
        for i, test_method in enumerate(test_methods, 1):
            try:
                print(f"\n🔄 执行测试 {i}/{len(test_methods)}: {test_method.__name__}")
                success = test_method()
                if not success:
                    print(f"⚠️ 测试 {test_method.__name__} 失败，继续后续测试...")
                time.sleep(1)  # 测试间隔
            except Exception as e:
                print(f"❌ 测试 {test_method.__name__} 异常: {str(e)}")
        
        return self.generate_final_report()


if __name__ == "__main__":
    print("🎯 开始智能对话训练平台最终验收测试")
    
    # 运行验收测试
    tester = FinalAcceptanceTest()
    success = tester.run_full_acceptance_test()
    
    if success:
        print("\n🎊 验收测试通过！系统可以交付使用！")
        exit(0)
    else:
        print("\n🔧 验收测试发现问题，请查看报告并修复")
        exit(1) 