import logging
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Like, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("likes_v4")

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

class LikesByUser(Resource):
    @jwt_required()
    
    def get(self, user_id=None):
        if not user_id:
            user, err = require_user()
            if err:
                return err
            user_id = user.id
        likes = Like.query.filter_by(user_id=user_id).all()
        return [{"id": l.id, "post_id": l.post_id} for l in likes], 200
