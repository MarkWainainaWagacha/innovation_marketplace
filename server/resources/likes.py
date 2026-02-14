import logging
from flask_restful import Resource
from models import Like

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("likes_v6")


class RecentLikes(Resource):
    def get(self, limit=10):
        
        likes = Like.query.order_by(Like.id.desc()).limit(limit).all()
        logger.info(f"Fetched {len(likes)} recent likes")
        return [
            {"id": l.id, "user_id": l.user_id, "post_id": l.post_id}
            for l in likes
        ], 200
