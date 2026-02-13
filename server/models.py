from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from datetime import datetime
from sqlalchemy import UniqueConstraint

metadata = MetaData()
db = SQLAlchemy(metadata=metadata)


class Merchandise(db.Model):
    __tablename__ = "merchandise"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

    orders = db.relationship("OrderMerchandise", back_populates="merchandise")

    # harmless method added
    def dummy_method_v3(self):
        return f"{self.name} dummy"
