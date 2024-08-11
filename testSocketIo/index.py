from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, send
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 存储聊天记录
messages = []


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/messages')
def get_messages():
    return jsonify(messages)


@socketio.on('message')
def handleMessage(msg):
    if msg != 'User has connected!':
        print('Message: ' + msg)
        messages.append(msg)
        print(f"messages: {messages}")
        send(msg, broadcast=True)
    else:
        print('asda')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=1880, debug=True, allow_unsafe_werkzeug=True)
