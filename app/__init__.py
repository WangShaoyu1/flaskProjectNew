from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_login import LoginManager
from app.config import Config
import os

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login = LoginManager()
login.login_view = 'auth_fun.login'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login.init_app(app)

    from app.models import User

    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes import main
    app.register_blueprint(main)

    from app.auth import auth_fun
    app.register_blueprint(auth_fun, url_prefix='/auth')

    from app.chat import chat_fun
    app.register_blueprint(chat_fun, url_prefix='/chat')

    from app.githubWebhooks import web_hooks
    app.register_blueprint(web_hooks, url_prefix='/github')

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
