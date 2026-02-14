import logging
from flask_restful import Resource
from models import db, Like

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("likes_v11")

class RemoveDuplicateLikes(Resource):
    def delete(self):
        seen = set()
        duplicates = []

        likes = Like.query.all()
        for like in likes:
            key = (like.user_id, like.post_id)
            if key in seen:
                duplicates.append(like)
            else:
                seen.add(key)

        for dup in duplicates:
            db.session.delete(dup)

        db.session.commit()
        logger.info(f"Removed {len(duplicates)} duplicate likes")
        return {"duplicates_removed": len(duplicates)}, 200
