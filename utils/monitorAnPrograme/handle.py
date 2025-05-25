import chardet
import psutil
from scapy.all import sniff, IP, TCP, Raw
import threading
import time
from collections import defaultdict
from decrypt import data_queue

# 配置区 ================================================
TARGET_PROCESS = "yuanbao.exe"  # 目标进程名（不区分大小写）
MONITOR_INTERVAL = 5  # 连接监控间隔（秒）
MAX_DISPLAY_LEN = 200  # 最大数据显示长度
# ======================================================

# 全局状态记录
connection_stats = defaultdict(lambda: {
    'sent': 0,
    'received': 0,
    'last_activity': time.time()
})


def get_target_pids():
    """获取目标进程的所有PID（带重试机制）"""
    for _ in range(3):  # 最多重试3次
        pids = [
            proc.info['pid']
            for proc in psutil.process_iter(['pid', 'name'])
            if proc.info['name'].lower() == TARGET_PROCESS.lower()
        ]
        if pids:
            return pids
        time.sleep(1)
    return []


def get_connections_by_pid(pid):
    """安全获取进程连接信息"""
    try:
        return psutil.Process(pid).connections(kind='inet')
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return []


def decode_payload(payload):
    """
    智能解码网络负载数据
    返回: (是否文本数据, 解码结果或十六进制字符串)
    """
    # 先尝试UTF-8（常见于现代协议）
    try:
        return True, payload.decode('utf-8')
    except UnicodeDecodeError:
        pass

    # 自动检测编码（仅当数据足够长时）
    if len(payload) > 32:
        try:
            result = chardet.detect(payload)
            if result['confidence'] > 0.7:
                return True, payload.decode(result['encoding'], errors='replace')
        except:
            pass

    # 最终回退方案：十六进制显示
    return False, payload.hex()


def format_data(data, is_text):
    """格式化输出数据"""
    if is_text:
        if len(data) > MAX_DISPLAY_LEN:
            return data[:MAX_DISPLAY_LEN] + "..."
        return data
    else:
        if len(data) > 40:
            return data[:40] + "..."
        return data


def packet_handler(packet):
    """核心数据包处理逻辑"""
    if IP not in packet or TCP not in packet:
        return

    src_ip = packet[IP].src
    dst_ip = packet[IP].dst
    src_port = packet[TCP].sport
    dst_port = packet[TCP].dport

    # 获取目标进程使用的所有端口
    target_ports = {
        conn.laddr.port
        for pid in get_target_pids()
        for conn in get_connections_by_pid(pid)
    }

    # 判断是否目标流量
    is_outbound = src_port in target_ports
    is_inbound = dst_port in target_ports
    if not (is_outbound or is_inbound):
        return

    # 更新连接统计
    conn_key = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}"
    if is_outbound:
        connection_stats[conn_key]['sent'] += len(packet[Raw].load) if Raw in packet else 0
    else:
        connection_stats[conn_key]['received'] += len(packet[Raw].load) if Raw in packet else 0
    connection_stats[conn_key]['last_activity'] = time.time()

    # 输出连接信息
    direction = "出站" if is_outbound else "入站"
    print(f"\n[{time.strftime('%H:%M:%S')}] {direction}连接 {src_ip}:{src_port} -> {dst_ip}:{dst_port}")

    # 处理负载数据
    if Raw in packet:
        is_text, decoded = decode_payload(packet[Raw].load)
        data_type = "文本" if is_text else "二进制"
        print(f"[{data_type}数据]", format_data(decoded, is_text))


def monitor_connections():
    """定时显示连接状态"""
    while True:
        active_pids = get_target_pids()
        print("\n" + "=" * 60)
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} 监控状态")
        print(f"目标进程: {TARGET_PROCESS} (PIDs: {active_pids if active_pids else '未运行'})")

        # 显示活动连接统计
        print("\n活动连接统计:")
        for conn, stats in connection_stats.items():
            if time.time() - stats['last_activity'] < 30:  # 只显示30秒内有活动的连接
                src_dst = conn.split('-')
                print(f"{src_dst[0]} -> {src_dst[1]} | "
                      f"发送: {stats['sent'] / 1024:.1f}KB | "
                      f"接收: {stats['received'] / 1024:.1f}KB")

        time.sleep(MONITOR_INTERVAL)


if __name__ == "__main__":
    # 检查权限
    try:
        psutil.Process().connections()
    except PermissionError:
        print("请以管理员/root权限运行！")
        exit(1)

    # 启动监控线程
    threading.Thread(target=monitor_connections, daemon=True).start()

    # 主线程抓包
    print(f"启动网络监控 (目标进程: {TARGET_PROCESS})")
    print("按Ctrl+C停止监控...")
    try:
        sniff(prn=packet_handler, filter="tcp", store=0)
    except KeyboardInterrupt:
        print("\n监控已停止")