import chardet
import psutil
from scapy.all import sniff, IP, TCP, Raw
import threading
import time
from collections import defaultdict
from decrypt import data_queue  # 导入共享队列

# 配置区 ================================================
TARGET_PROCESS = "yuanbao.exe"  # 目标进程名
MONITOR_INTERVAL = 5  # 监控间隔


# ======================================================

def packet_handler(packet):
    """处理从mitmdump队列获取的解密数据"""
    if not data_queue.empty():
        decrypted = data_queue.get()
        print(f"\n[解密成功] {decrypted['src_ip']} -> {decrypted['dst_ip']}")
        print(f"URL: {decrypted['url']}\nData: {decrypted['data'][:200]}...")


if __name__ == "__main__":
    # 启动mitmdump（需手动运行）
    print("请先启动mitmdump: mitmdump -p 8888 -s decrypt.py --ssl-insecure")

    # 启动scapy监听
    print("启动scapy监控解密数据...")
    sniff(prn=packet_handler, filter="tcp", store=0)
