from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from datetime import datetime
from sqlalchemy import UniqueConstraint

metadata = MetaData()
db = SQLAlchemy(metadata=metadata)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)

    projects = db.relationship("ProjectCategory", back_populates="projects")

    # harmless method added
    def dummy_category_v8(self):
        return f"{self.name} category v8"
