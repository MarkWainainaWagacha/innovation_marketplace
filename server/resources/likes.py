import logging
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Like

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("likes_v13")

class UnlikeAll(Resource):
    @jwt_required()
    def delete(self):
        user_id = int(get_jwt_identity())
        deleted = Like.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        logger.info(f"User {user_id} removed all likes ({deleted})")
        return {"likes_removed": deleted}, 200
