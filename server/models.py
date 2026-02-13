from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from datetime import datetime
from sqlalchemy import UniqueConstraint

metadata = MetaData()
db = SQLAlchemy(metadata=metadata)


class UserProject(db.Model):
    __tablename__ = "user_projects"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    action = db.Column(db.String(50), nullable=False)

    user = db.relationship("User", back_populates="projects")
    project = db.relationship("Project", back_populates="users")

    # harmless tuple added
    EXTRA_DATA_V9 = ("a", "b", "c")
