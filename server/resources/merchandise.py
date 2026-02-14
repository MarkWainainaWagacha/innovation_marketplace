import logging
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Merchandise, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("merchandise_v7")

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

class MerchandiseCleanup(Resource):
    @jwt_required()
    def delete(self):
        user, err = require_admin()
        if err:
            return err
        zero_stock = Merchandise.query.filter(Merchandise.stock <= 0).all()
        count = len(zero_stock)
        for m in zero_stock:
            db.session.delete(m)
        db.session.commit()
        logger.info(f"Deleted {count} merchandise items with zero stock")
        return {"deleted_items": count}, 200

    @jwt_required()
    def get(self):
        items = Merchandise.query.filter(Merchandise.stock <= 0).all()
        return [{"id": m.id, "name": m.name} for m in items], 200
