from flask import Flask
from server.extensions import db, jwt, bcrypt
from server.auth_routes import auth_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moringa.db'
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

db.init_app(app)
jwt.init_app(app)
bcrypt.init_app(app)

app.register_blueprint(auth_bp, url_prefix='/auth')

if __name__ == "__main__":
    app.run(debug=True)
