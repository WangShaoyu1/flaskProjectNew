from flask import Flask, redirect, url_for, request, Response
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_login import LoginManager
from app.config import Config
import os
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login = LoginManager()
login.login_view = 'auth_fun.login'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, resources={r"/*": {"origins": "*"}})

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login.init_app(app)

    from app.models import User

    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes import main
    app.register_blueprint(main, url_prefix='/gpt')

    from app.auth import auth_fun
    app.register_blueprint(auth_fun, url_prefix='/gpt/auth')

    from app.chat import chat_fun
    app.register_blueprint(chat_fun, url_prefix='/gpt/chat')

    from app.githubWebhooks import web_hooks
    app.register_blueprint(web_hooks, url_prefix='/github')

    @app.route('/')
    def index():
        return redirect(url_for('main.home'))

    @app.before_request
    def before_request_func():
        if request.method == 'OPTIONS':
            return _build_cors_prelight_response()

    @app.after_request
    def add_header(response):
        if response.content_type == 'text/html; charset=utf-8':
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
        elif response.content_type == 'application/json; charset=utf-8':
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response

    def _build_cors_prelight_response():
        # 添加响应的基本方法
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        return response

    @app.cli.command('reset_db')
    def reset_db():
        db_path = os.path.join(app.instance_path, 'chat_app.db')

        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Deleted database {db_path}")

        with app.app_context():
            db.create_all()
            print("Recreated all tables")

    return app
