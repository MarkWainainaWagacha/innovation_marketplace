import logging
from flask_restful import Resource
from sqlalchemy import func
from models import db, Like

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("likes_v12")

class TrendingPosts(Resource):
    def get(self):
        results = db.session.query(
            Like.post_id,
            func.count(Like.id).label("count")
        ).group_by(Like.post_id)\
         .order_by(func.count(Like.id).desc())\
         .limit(3).all()

        trending = [{"post_id": r.post_id, "likes": r.count} for r in results]
        logger.info("Fetched trending posts")
        return trending, 200
