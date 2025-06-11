from flask import Flask, request
from datetime import datetime
import os

app = Flask(__name__)

# 获取当前 Python 文件的目录路径，并拼接日志文件名
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aiui_log.txt')


@app.route('/log', methods=['GET', 'POST'])
def log():
    try:
        data = request.json
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp} [{data['tag']}] {data['message']}\n"

        # 写入日志文件（追加模式）
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        return {'status': 'success'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500


if __name__ == '__main__':
    # 确保日志文件存在
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w', encoding='utf-8').close()

    app.run(host='0.0.0.0', port=5002)
