#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CDN管理工具
用于测试不同CDN的可用性并切换CDN配置
"""

import requests
import time
import sys
from cdn_config import CDN_CONFIGS, CURRENT_CDN

def test_url(url, timeout=5):
    """测试URL的可访问性和响应时间"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        end_time = time.time()
        
        if response.status_code == 200:
            response_time = round((end_time - start_time) * 1000, 2)
            return True, response_time
        else:
            return False, None
    except Exception as e:
        return False, str(e)

def test_cdn_config(cdn_name, config):
    """测试单个CDN配置的所有URL"""
    print(f"\n🔍 测试 {config['name']} ({cdn_name})")
    print("-" * 50)
    
    urls_to_test = [
        ("Swagger JS", config["swagger_js"]),
        ("Swagger CSS", config["swagger_css"]),
        ("ReDoc JS", config["redoc_js"])
    ]
    
    all_success = True
    total_time = 0
    
    for name, url in urls_to_test:
        success, result = test_url(url)
        if success:
            print(f"✅ {name}: {result}ms")
            total_time += result
        else:
            print(f"❌ {name}: 失败 ({result})")
            all_success = False
    
    if all_success:
        avg_time = round(total_time / len(urls_to_test), 2)
        print(f"🎯 平均响应时间: {avg_time}ms")
        return True, avg_time
    else:
        print("⚠️  该CDN存在访问问题")
        return False, None

def test_all_cdns():
    """测试所有CDN配置"""
    print("🌐 开始测试所有CDN配置...")
    print("=" * 60)
    
    results = {}
    
    for cdn_name, config in CDN_CONFIGS.items():
        success, avg_time = test_cdn_config(cdn_name, config)
        results[cdn_name] = {
            "success": success,
            "avg_time": avg_time,
            "config": config
        }
    
    # 显示测试结果汇总
    print("\n📊 测试结果汇总")
    print("=" * 60)
    
    successful_cdns = [(name, data) for name, data in results.items() if data["success"]]
    successful_cdns.sort(key=lambda x: x[1]["avg_time"])
    
    if successful_cdns:
        print("✅ 可用的CDN (按响应速度排序):")
        for i, (name, data) in enumerate(successful_cdns, 1):
            print(f"{i}. {data['config']['name']} ({name}): {data['avg_time']}ms")
        
        # 推荐最快的CDN
        best_cdn = successful_cdns[0]
        print(f"\n🚀 推荐使用: {best_cdn[1]['config']['name']} ({best_cdn[0]})")
        print(f"   平均响应时间: {best_cdn[1]['avg_time']}ms")
    else:
        print("❌ 所有CDN都无法访问，建议使用本地文件")
    
    failed_cdns = [name for name, data in results.items() if not data["success"]]
    if failed_cdns:
        print(f"\n⚠️  无法访问的CDN: {', '.join(failed_cdns)}")
    
    return results

def update_cdn_config(cdn_name):
    """更新CDN配置文件"""
    if cdn_name not in CDN_CONFIGS:
        print(f"❌ 未知的CDN配置: {cdn_name}")
        return False
    
    try:
        # 读取当前配置文件
        with open('cdn_config.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换CURRENT_CDN的值
        old_line = f'CURRENT_CDN = "{CURRENT_CDN}"'
        new_line = f'CURRENT_CDN = "{cdn_name}"'
        
        if old_line in content:
            new_content = content.replace(old_line, new_line)
            
            # 写入新配置
            with open('cdn_config.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ CDN配置已更新为: {CDN_CONFIGS[cdn_name]['name']}")
            print("📌 请重启服务以使配置生效")
            return True
        else:
            print("❌ 无法找到CURRENT_CDN配置行")
            return False
            
    except Exception as e:
        print(f"❌ 更新配置文件失败: {e}")
        return False

def show_usage():
    """显示使用说明"""
    print("""
🛠️  CDN管理工具使用说明

命令格式:
  python manage_cdn.py [命令]

可用命令:
  test        - 测试所有CDN的可用性和响应速度
  list        - 显示所有可用的CDN配置
  switch      - 交互式切换CDN配置
  current     - 显示当前使用的CDN
  
示例:
  python manage_cdn.py test     # 测试所有CDN
  python manage_cdn.py switch   # 切换CDN配置
""")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "test":
        test_all_cdns()
    
    elif command == "list":
        print("📋 可用的CDN配置:")
        print("-" * 40)
        for name, config in CDN_CONFIGS.items():
            current_mark = " (当前)" if name == CURRENT_CDN else ""
            print(f"• {name}: {config['name']}{current_mark}")
            print(f"  {config['description']}")
            print()
    
    elif command == "current":
        current_config = CDN_CONFIGS[CURRENT_CDN]
        print(f"当前使用的CDN: {current_config['name']} ({CURRENT_CDN})")
        print(f"描述: {current_config['description']}")
    
    elif command == "switch":
        print("🔄 CDN切换工具")
        print("-" * 30)
        
        # 显示所有选项
        cdn_list = list(CDN_CONFIGS.keys())
        for i, name in enumerate(cdn_list, 1):
            config = CDN_CONFIGS[name]
            current_mark = " (当前)" if name == CURRENT_CDN else ""
            print(f"{i}. {config['name']} ({name}){current_mark}")
        
        try:
            choice = input("\n请选择CDN (输入数字): ").strip()
            choice_idx = int(choice) - 1
            
            if 0 <= choice_idx < len(cdn_list):
                selected_cdn = cdn_list[choice_idx]
                if selected_cdn == CURRENT_CDN:
                    print("💡 已经是当前CDN，无需切换")
                else:
                    # 先测试选择的CDN
                    print(f"\n🔍 测试选择的CDN...")
                    config = CDN_CONFIGS[selected_cdn]
                    success, avg_time = test_cdn_config(selected_cdn, config)
                    
                    if success:
                        confirm = input(f"\n确认切换到 {config['name']} 吗? (y/N): ").strip().lower()
                        if confirm in ['y', 'yes']:
                            update_cdn_config(selected_cdn)
                        else:
                            print("❌ 取消切换")
                    else:
                        print("⚠️  该CDN存在访问问题，建议选择其他CDN")
            else:
                print("❌ 无效的选择")
                
        except (ValueError, KeyboardInterrupt):
            print("\n❌ 操作已取消")
    
    else:
        print(f"❌ 未知命令: {command}")
        show_usage()

if __name__ == "__main__":
    main() 