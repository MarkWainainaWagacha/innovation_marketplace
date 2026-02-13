from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from datetime import datetime
from sqlalchemy import UniqueConstraint

metadata = MetaData()
db = SQLAlchemy(metadata=metadata)


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    video = db.Column(db.String(255), nullable=False)
    github_url = db.Column(db.String(255), nullable=False)
    technologies = db.Column(db.String(255), nullable=False)
    submitted_name = db.Column(db.String(100), nullable=False)
    thumbnail_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
