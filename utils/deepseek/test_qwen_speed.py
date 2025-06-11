import os
import time
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from utils import util, log

# 记录开始时间
start_time = time.time()
first_char_time = None
full_response = []

# 加载.env文件中的环境变量
load_dotenv()


# 加载tools.json文件
def load_tools_config():
    tools_path = Path(__file__).parent / "tools.json"
    try:
        with open(tools_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ 警告：未找到工具配置文件 {tools_path}")
        return None
    except json.JSONDecodeError:
        print(f"⚠️ 警告：工具配置文件 {tools_path} 格式错误")
        return None


# 获取工具配置
tools_config = []

client = OpenAI(
    api_key=os.getenv("QWEN_DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",

)

# 构造请求参数
request_params = {
    "model": "qwen-plus",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "港股通阿里巴巴今天股价怎么样？"},
    ],
    "stream": True,
    "max_tokens": 500,
    "extra_body": {"enable_thinking": False, "enable_search": True},
}

# 如果有工具配置，添加到请求参数中
# 如果存在工具配置则添加
if tools_config:
    request_params["tools"] = tools_config.get("tools", [])
    request_params["tool_choice"] = tools_config.get("tool_choice", "auto")
    # print("✅ 已加载工具配置:", json.dumps(tools_config, indent=2, ensure_ascii=False))

# 发起流式请求
stream = client.chat.completions.create(**request_params)

print("\n流式响应开始：")
for chunk in stream:
    # 获取当前chunk内容
    content = chunk.choices[0].delta.content or ""

    # 记录首字符到达时间(TTFB)
    if content and first_char_time is None:
        first_char_time = time.time() - start_time
        print(f"\n[首字符到达] {first_char_time * 1000:.2f}ms")

    # 收集完整响应
    full_response.append(content)
    print(content, end="", flush=True)  # 实时输出

    # 检查是否包含工具调用
    if chunk.choices[0].delta.tool_calls:
        print("\n🔧 检测到工具调用:", chunk.choices[0].delta.tool_calls)

# 计算完整响应时间
end_time = time.time()
total_time = (end_time - start_time) * 1000  # 毫秒

# 性能报告
# 性能报告
performance_report = f"""
{'=' * 40}
首字符时间(TTFB): {first_char_time * 1000:.2f}ms
完整响应时间: {total_time:.2f}ms
总字符数: {len(''.join(full_response))}
生成速度: {len(''.join(full_response)) / total_time * 1000:.2f} char/s
完整响应: {''.join(full_response)}
{'=' * 40}
"""
util.write_to_file("performance.log", performance_report)
