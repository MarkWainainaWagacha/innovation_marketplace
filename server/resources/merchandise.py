import logging
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Merchandise, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("merchandise_v6")

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

class MerchandiseStock(Resource):
    @jwt_required()
    def patch(self, id):
        user, err = require_admin()
        if err:
            return err
        item = Merchandise.query.get_or_404(id)
        data = request.get_json(silent=True) or {}
        if "stock" in data:
            item.stock = data["stock"]
            db.session.commit()
            logger.info(f"Stock updated: {item.name} -> {item.stock}")
        return {"id": item.id, "stock": item.stock}, 200

    @jwt_required()
    def get(self):
        items = Merchandise.query.all()
        return [{"id": m.id, "stock": m.stock} for m in items], 200
