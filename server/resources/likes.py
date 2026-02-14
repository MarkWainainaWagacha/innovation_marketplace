import logging
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Like, User, Post  # Assuming likes are for posts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("likes_v1")

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

class LikeList(Resource):
    @jwt_required()
    def get(self):
        likes = Like.query.all()
        return [{"id": l.id, "user_id": l.user_id, "post_id": l.post_id} for l in likes], 200

    @jwt_required()
    def post(self):
        user, err = require_user()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        post_id = data.get("post_id")
        if not post_id:
            return {"error": "post_id is required"}, 400
        like = Like(user_id=user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()
        logger.info(f"User {user.id} liked post {post_id}")
        return {"message": "Post liked"}, 201

class LikeItem(Resource):
    @jwt_required()
    def delete(self, id):
        user, err = require_user()
        if err:
            return err
        like = Like.query.get_or_404(id)
        if like.user_id != user.id:
            return {"error": "Cannot delete others' likes"}, 403
        db.session.delete(like)
        db.session.commit()
        logger.info(f"User {user.id} removed like {id}")
        return {"message": "Like removed"}, 200
