import logging
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Like, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("likes_v7")

def require_admin():
    raw_id = get_jwt_identity()
    try:
        user_id = int(raw_id)
    except:
        return None, ({"error": "Invalid token"}, 401)
    user = User.query.get(user_id)
    if not user or not user.role or user.role.name != "admin":
        return None, ({"error": "Admin access required"}, 403)
    return user, None

class ClearPostLikes(Resource):
    @jwt_required()
    def delete(self, post_id):
        user, err = require_admin()

        
        if err:
            return err
        deleted = Like.query.filter_by(post_id=post_id).delete()
        db.session.commit()
        logger.info(f"Deleted {deleted} likes for post {post_id}")
        return {"deleted_likes": deleted}, 200
