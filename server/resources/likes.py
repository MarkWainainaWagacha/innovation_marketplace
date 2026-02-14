import logging
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Like, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("likes_v8")

class BatchLike(Resource):
    @jwt_required()
    def post(self):
        user_id = int(get_jwt_identity())
        data = request.get_json(silent=True) or {}
        post_ids = data.get("post_ids", [])

        created = 0
        for pid in post_ids:
            exists = Like.query.filter_by(user_id=user_id, post_id=pid).first()
            if not exists:
                db.session.add(Like(user_id=user_id, post_id=pid))
                created += 1

        db.session.commit()
        logger.info(f"User {user_id} batch liked {created} posts")
        return {"likes_added": created}, 201
