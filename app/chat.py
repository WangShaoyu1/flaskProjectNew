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
    return jsonify([{'conversation_id': chat.conversation_id, 'title': chat.title} for chat in chats])


@chat.route('/<string:conversation_id>', methods=['GET'])
@login_required
def view_chat(conversation_id):
    return render_template('chat/index.html', conversation_id=conversation_id)


@chat.route('/api/get_messages/<string:conversation_id>', methods=['GET'])
@login_required
def get_messages(conversation_id):
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp.asc()).all()
    return jsonify([{'content': message.content, 'from_user': message.from_user} for message in messages])


@chat.route('/api/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.json
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
    chat_history = Message.query.filter_by(conversation_id=chat.conversation_id).order_by(Message.timestamp.asc()).all()
    messages = [{"role": "user" if msg.from_user else "assistant", "content": msg.content} for msg in chat_history]

    # Append the current user message
    # messages.append({"role": "user", "content": content})

    print(f"messages: {messages}")
    util.write_to_file('./temp_data_dir/result_1.txt', str(messages))
    # Call OpenAI API
    client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'], base_url=current_app.config['OPENAI_BASE_URL'])
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    bot_response = response.choices[0].message.content

    # Add bot response to the database
    bot_message = Message(content=bot_response, from_user=False, conversation_id=chat.conversation_id,
                          sender_id=current_user.id)
    db.session.add(bot_message)
    db.session.commit()

    return jsonify(
        {'status': 'success', 'conversation_id': chat.conversation_id, 'message': 'Message sent successfully'})


@chat.route('/api/chat/<string:conversation_id>', methods=['DELETE'])
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
