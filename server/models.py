from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from datetime import datetime
from sqlalchemy import UniqueConstraint

metadata = MetaData()
db = SQLAlchemy(metadata=metadata)


class ProjectLike(db.Model):
    __tablename__ = "project_likes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
    project = db.relationship("Project")

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_user_project_like"),
    )

    # harmless dummy method
    def dummy_method_v6(self):
        return "This is harmless v6"
