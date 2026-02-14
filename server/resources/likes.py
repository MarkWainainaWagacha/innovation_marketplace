import logging
from flask_restful import Resource
from models import db, Like
from sqlalchemy import func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("likes_v5")

class TopLikedPosts(Resource):
    def get(self, limit=5):
        result = db.session.query(
            Like.post_id, func.count(Like.id).label("like_count")
        ).group_by(Like.post_id).order_by(func.count(Like.id).desc()).limit(limit).all()
        top_posts = [{"post_id": r.post_id, "likes": r.like_count} for r in result]
        logger.info(f"Top {limit} liked posts retrieved")
        return top_posts, 200
