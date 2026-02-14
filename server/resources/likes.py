import logging
from flask_restful import Resource
from models import Like

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("likes_v2")

class LikeCount(Resource):
    def get(self, post_id):
        count = Like.query.filter_by(post_id=post_id).count()
        logger.info(f"Post {post_id} has {count} likes")
        return {"post_id": post_id, "likes_count": count}, 200
