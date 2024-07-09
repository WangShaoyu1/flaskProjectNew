from app import create_app, db

app = create_app()


@app.before_request
def initialize_database():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, port=5002, host='0.0.0.0')
