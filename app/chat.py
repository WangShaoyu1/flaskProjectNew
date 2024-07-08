from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Chat, Message
import openai
from openai import OpenAI
import uuid
from litellm import completion
from utils import util
chat = Blueprint('chat', __name__)


@chat.route('/api/get_chats', methods=['GET'])
@login_required
def get_chats():
    chats = Chat.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'id': chat.id, 'title': chat.title} for chat in chats])


@chat.route('/<int:chat_id>', methods=['GET'])
@login_required
def view_chat(chat_id):
    return render_template('chat/index.html', chat_id=chat_id)


@chat.route('/api/get_messages/<int:chat_id>', methods=['GET'])
@login_required
def get_messages(chat_id):
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp.asc()).all()
    return jsonify([{'content': message.content, 'from_user': message.from_user} for message in messages])


@chat.route('/api/send_message/<int:chat_id>', methods=['POST'])
@login_required
def send_message(chat_id):
    data = request.json
    content = data.get('message', '')
    if not content:
        return jsonify({'status': 'error', 'message': 'Invalid data'})

    chat = Chat.query.get(chat_id)
    if not chat:
        # If chat doesn't exist, create a new chat
        title = content[:10]
        conversation_id = str(uuid.uuid4())
        chat = Chat(title=title, user_id=current_user.id, conversation_id=conversation_id)
        db.session.add(chat)
        db.session.commit()

    # Add user message to the database
    user_message = Message(content=content, from_user=True, chat_id=chat.id, sender_id=current_user.id)
    db.session.add(user_message)
    db.session.commit()

    # Get chat history for the current chat session
    chat_history = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp.asc()).all()
    messages = [{"role": "user" if msg.from_user else "assistant", "content": msg.content} for msg in chat_history]

    # Append the current user message
    messages.append({"role": "user", "content": content})

    print(messages)
    util.write_to_file('./temp_data_dir/result_1.txt', str(messages))
    # Call OpenAI API
    client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'], base_url=current_app.config['OPENAI_BASE_URL'])
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    bot_response = response.choices[0].message.content

    # Add bot response to the database
    bot_message = Message(content=bot_response, from_user=False, chat_id=chat.id, sender_id=current_user.id)
    db.session.add(bot_message)
    db.session.commit()

    return jsonify({'status': 'success', 'chat_id': chat.id, 'message': 'Message sent successfully'})
