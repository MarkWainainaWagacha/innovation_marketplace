import logging
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Merchandise, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("merchandise_v5")

def require_admin():
    raw_id = get_jwt_identity()
    try:
        user_id = int(raw_id)
    except:
        return None, ({"error": "Invalid token identity"}, 401)
    user = User.query.get(user_id)
    if not user or not user.role or user.role.name != "admin":
        return None, ({"error": "Admin access required"}, 403)
    return user, None

class MerchandiseCreate(Resource):
    @jwt_required()
    def post(self):
        user, err = require_admin()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        item = Merchandise(
            name=data.get("name", "").strip(),
            description=data.get("description", "").strip(),
            price=data.get("price", 0),
            stock=data.get("stock", 0),
            image_url=data.get("image_url", "").strip()
        )
        db.session.add(item)
        db.session.commit()
        logger.info(f"Merchandise created: {item.name}")
        return {"message": "Merchandise created"}, 201
