from mitmproxy import http
from queue import Queue
import threading

# 共享队列（用于与scapy通信）
data_queue = Queue()

def response(flow: http.HTTPFlow):
    """解密HTTPS响应并存入队列"""
    if flow.response and flow.response.content:
        data_queue.put({
            'url': flow.request.url,
            'data': flow.response.text,  # 明文数据
            'src_ip': flow.client_conn.address[0],
            'dst_ip': flow.server_conn.address[0]
        })

# 启动线程监听队列（可选）
def start_consumer():
    while True:
        if not data_queue.empty():
            print("[解密数据]", data_queue.get())

threading.Thread(target=start_consumer, daemon=True).start()