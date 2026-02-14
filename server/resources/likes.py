import logging
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Like

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("likes_v9")
 ###
class CheckLike(Resource):
    @jwt_required()
    def get(self, post_id):
        user_id = int(get_jwt_identity())
        exists = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
        logger.info(f"Checked like for user {user_id} on post {post_id}")
        return {"liked": bool(exists)}, 200
