import logging
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Like, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("likes_v3")

def require_user():
    raw_id = get_jwt_identity()
    try:
        user_id = int(raw_id)
    except:
        return None, ({"error": "Invalid token identity"}, 401)
    user = User.query.get(user_id)
    if not user:
        return None, ({"error": "User not found"}, 404)
    return user, None

class LikeToggle(Resource):
    @jwt_required()
    def post(self):
        user, err = require_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        post_id = data.get("post_id")
        if not post_id:
            return {"error": "post_id is required"}, 400
        existing = Like.query.filter_by(user_id=user.id, post_id=post_id).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            logger.info(f"User {user.id} unliked post {post_id}")
            return {"message": "Post unliked"}, 200
        like = Like(user_id=user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()
        logger.info(f"User {user.id} liked post {post_id}")
        return {"message": "Post liked"}, 201
