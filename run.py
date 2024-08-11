from app import create_app, db
from app.socketio import socketio

app = create_app()
app.config['SECRET_KEY'] = 'secret!'

socketio.init_app(app, cors_allowed_origins="*")


@app.before_request
def initialize_database():
    db.create_all()


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5002, host='0.0.0.0')
