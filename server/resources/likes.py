import logging
from flask_restful import Resource
from models import Like

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("likes_v10")

class TotalLikes(Resource):
    def get(self):
        total = Like.query.count()
        logger.info(f"Total likes in system: {total}")
        return {"total_likes": total}, 200
