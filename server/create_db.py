from server.app import app
from server.extensions import db
from server import models  # make sure this imports all your models

with app.app_context():
    db.create_all()
    print("Tables created successfully!")
