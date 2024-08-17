from flask_socketio import SocketIO, emit, send, join_room

socketio = SocketIO()


@socketio.on('connect', namespace='/smart_client')
def handle_connect():
    print("web客户端已连接:smart_client")
    emit('Server send --connect', {'message': '连接已建立'})


@socketio.on('message', namespace='/smart_client')
def handle_send_message(message):
    print(f'收到客户端的消息: {message}')
    emit('my_message', message, broadcast=True)


@socketio.on('disconnect', namespace='/smart_client')
def handle_disconnect():
    print("客户端已断开连接:smart_client")


@socketio.on('my_h5_event', namespace='/smart_client')
def handle_connect(data):
    print("my_h5_event来信息了:", data)
    emit('my_message', {'message': data})


@socketio.on('from_smart_device_event', namespace='/smart_client')
def handle_connect(data):
    print("smart_device来信息了:", data)
    send("收到了，吉山111")


@socketio.on('join_room', namespace='/smart_client')
def handle_join(data):
    print("join_room:", data)
    room = data['room']
    join_room(room)
    emit('message', f"New user has joined the room '{room}'.")
