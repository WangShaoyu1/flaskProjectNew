from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
import openai
from app.models import User, Chat, Message
from app.forms import ChatForm, MessageForm
from app import db

chat = Blueprint('chat', __name__)


@chat.route("/chat-list", methods=["GET"])
@login_required
def index():
    form = ChatForm()
    chats = Chat.query.filter_by(user_id=current_user.id).all()
    return render_template('chat.html', chats=chats, messages=[], title='Chat', form=form)


@chat.route("/chat/<int:conversation_id>", methods=['GET'])
@login_required
def chat_detail(conversation_id):
    chat = Chat.query.filter_by(conversation_id=conversation_id, user_id=current_user.id).first_or_404()
    messages = Message.query.filter_by(chat_id=chat.id).all()
    return render_template('chat.html', chats=[], messages=messages, chat=chat)


@chat.route("/api/send_message", methods=['POST'])
def send_message():
    data = request.get_json()
    conversation_id = data['conversation_id']
    message_text = data['message']
    print(f"conversation_id: {conversation_id}, message_text: {message_text}")
    chat = Chat.query.filter_by(conversation_id=conversation_id, user_id=current_user.id).first_or_404()
    message = Message(chat_id=chat.id, sender=current_user.username, message=message_text)
    db.session.add(message)
    db.session.commit()

    openai.api_key = current_app.config['OPENAI_API_KEY']
    openai.api_base = current_app.config['OPENAI_BASE_URL']
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": message_text}
        ]
    )
    reply = response.choices[0].message['content']

    ai_message = Message(chat_id=chat.id, sender='AI', message=reply)
    db.session.add(ai_message)
    db.session.commit()

    return jsonify({'message': reply})
