# server/app.py
from flask import Flask
from server.extensions import db, jwt, bcrypt
from server.auth_routes import auth_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'  # example
app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # change this

# initialize extensions
db.init_app(app)
jwt.init_app(app)
bcrypt.init_app(app)

# register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')

if __name__ == '__main__':
    app.run(debug=True)
