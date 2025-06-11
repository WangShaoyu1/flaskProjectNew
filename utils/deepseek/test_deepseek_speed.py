import time
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com")

# 记录请求开始时间
start_time = time.time()
first_char_received = False
first_char_time = None
full_response = []

# 发起流式请求
stream = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    stream=True  # 启用流式返回
)

print("Streaming response (data: xxx format):")
for chunk in stream:
    # 记录第一个字符到达时间（TTFB）
    if not first_char_received:
        first_char_time = time.time() - start_time
        first_char_received = True
        print(f"\n[TTFB] First chunk received: {first_char_time * 1000:.2f}ms")

    # 获取当前 chunk 的内容
    content = chunk.choices[0].delta.content or ""
    full_response.append(content)

    # 以 `data: xxx` 格式实时输出
    print(f"data: {content}")

# 计算完整响应时间
end_time = time.time()
total_time = (end_time - start_time) * 1000  # 转换为毫秒

# 输出统计信息
print("\n[Performance Metrics]")
print(f"TTFB (First chunk): {first_char_time * 1000:.2f}ms")
print(f"Total time (All data): {total_time:.2f}ms")
print(f"Full response: {''.join(full_response)}")
