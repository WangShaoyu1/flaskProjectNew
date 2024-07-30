from flask import Blueprint, render_template, jsonify, request, current_app, Response, stream_with_context

from flask_login import login_required, current_user
from app import db
from app.models import Chat, Message
from openai import OpenAI
import uuid
import time
from utils import util, log

chat_fun = Blueprint('chat', __name__)


@chat_fun.route('/api/get_chats', methods=['GET'])
@login_required
def get_chats():
    chats = Chat.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'conversation_id': elem.conversation_id, 'title': elem.title} for elem in chats])


@chat_fun.route('/<string:conversation_id>', methods=['GET'])
@login_required
def view_chat(conversation_id):
    return render_template('chat/index.html', conversation_id=conversation_id)


@chat_fun.route('/api/get_messages/<string:conversation_id>', methods=['GET'])
@login_required
def get_messages(conversation_id):
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp.asc()).all()
    return jsonify([{'content': message.content, 'from_user': message.from_user} for message in messages])


@chat_fun.route('/api/send_message', methods=['POST'])
@login_required
def send_message_no_stream():
    data = request.json
    content = data.get('message', '')
    conversation_id = data.get('conversation_id', '')
    if not content:
        return jsonify({'status': 'error', 'message': 'Empty data'})

    chat = Chat.query.filter_by(conversation_id=conversation_id).first()
    # If chat doesn't exist, create a new chat
    if not chat:
        # If chat doesn't exist, create a new chat
        title = content[:10]
        conversation_id = str(uuid.uuid4())
        chat = Chat(title=title, user_id=current_user.id, conversation_id=conversation_id)
        db.session.add(chat)
        db.session.commit()

    # Add user message to the database
    user_message = Message(content=content, from_user=True, conversation_id=chat.conversation_id,
                           sender_id=current_user.id)
    db.session.add(user_message)
    db.session.commit()

    # Get chat history for the current chat session
    chat_history = Message.query.filter_by(conversation_id=chat.conversation_id).order_by(Message.timestamp.asc()).all()
    messages = [{"role": "user" if msg.from_user else "assistant", "content": msg.content} for msg in chat_history]

    # Record the time before sending the request
    start_time = time.time()

    # Call OpenAI API
    client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'], base_url=current_app.config['OPENAI_BASE_URL'])
    response = client.chat.completions.create(
        model=current_app.config['MODEL_NAME'],
        messages=messages
    )
    bot_response = response.choices[0].message.content

    # Record the time after receiving the response
    end_time = time.time()

    # Add bot response to the database
    bot_message = Message(content=bot_response, from_user=False, conversation_id=chat.conversation_id,
                          sender_id=current_user.id)
    db.session.add(bot_message)
    db.session.commit()

    # add the process data to the file
    util.write_to_file('./temp_data_dir/result_1.txt',
                       f'----------send_message_no_stream--{conversation_id}---------\n')
    util.write_to_file('./temp_data_dir/result_1.txt',
                       str(messages + [({"role": "assistant", "content": bot_response})]), True)
    util.write_to_file('./temp_data_dir/result_1.txt', f'\n本次请求耗时{round(end_time - start_time, 3)}秒\n')

    return jsonify({'status': 'success', 'conversation_id': chat.conversation_id,
                    'chat_data': {'user_message': content, 'bot_message': bot_response},
                    'message': 'Message sent successfully'})


@chat_fun.route('/api/send_message/stream', methods=['GET'])
def send_message_stream():
    data = request.args
    content = data.get('message', '')
    conversation_id = data.get('conversation_id', '')

    if not content:
        return jsonify({'status': 'error', 'message': 'Invalid data'})

    chat = Chat.query.filter_by(conversation_id=conversation_id).first()
    # If chat doesn't exist, create a new chat
    if not chat:
        # If chat doesn't exist, create a new chat
        title = content[:10]
        conversation_id = str(uuid.uuid4())
        chat = Chat(title=title, user_id=current_user.id, conversation_id=conversation_id)
        db.session.add(chat)
        db.session.commit()

    # Add user message to the database
    user_message = Message(content=content, from_user=True, conversation_id=chat.conversation_id,
                           sender_id=current_user.id)
    db.session.add(user_message)
    db.session.commit()

    # Get chat history for the current chat session
    chat_history = Message.query.filter_by(conversation_id=chat.conversation_id).order_by(
        Message.timestamp.asc()).all()
    messages = [{"role": "user" if msg.from_user else "assistant", "content": msg.content} for msg in chat_history]

    return Response(stream_openai_response(messages, conversation_id), mimetype='text/event-stream')


@chat_fun.route('/api/chat/<string:conversation_id>', methods=['DELETE'])
@login_required
def delete_chat(conversation_id):
    chat = Chat.query.filter_by(conversation_id=conversation_id).first()
    if not chat or chat.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Chat not found or unauthorized'}), 404

    # Delete all messages related to this chat
    Message.query.filter_by(conversation_id=conversation_id).delete()

    # Delete the chat itself
    db.session.delete(chat)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Chat deleted successfully'})


def stream_openai_response(messages, conversation_id):
    # Record the time before sending the request
    start_time = time.time()

    def generate():
        bot_response = ''
        # Call OpenAI API
        client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'], base_url=current_app.config['OPENAI_BASE_URL'])
        stream = client.chat.completions.create(
            model=current_app.config['MODEL_NAME'],
            messages=messages,
            stream=True
        )
        # Record the time after receiving the response
        end_time_start = time.time()
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="")
                bot_response += chunk.choices[0].delta.content
                yield f"data:{chunk.choices[0].delta.content}\n\n"
            else:
                # yield f"data:end\n\n"
                yield f'data:{{"is_last_char": true, "conversation_id": "{conversation_id}"}}\n\n'
        # Add bot response to the database
        bot_message = Message(content=bot_response, from_user=False, conversation_id=conversation_id,
                              sender_id=current_user.id)
        db.session.add(bot_message)
        db.session.commit()

        end_time_end = time.time()

        logger = log.setup_structlog("logs/example.log")
        logger.info(f'----------send_message_stream--{conversation_id}---------')
        logger.info(str(messages + [({"role": "assistant", "content": bot_response})]))
        logger.info(f'----------本次首字符请求耗时{round(end_time_start - start_time, 3)}秒----------')
        logger.info(f'----------本次完整请求耗时{round(end_time_end - start_time, 3)}秒----------')

    return stream_with_context(generate())
