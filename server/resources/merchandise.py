import logging
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Merchandise, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("merchandise_v3")

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

class MerchandiseListV3(Resource):
    def get(self):
        items = Merchandise.query.filter(Merchandise.stock > 0).all()
        return [
            {"id": m.id, "name": m.name, "price": float(m.price), "stock": m.stock}
            for m in items
        ], 200

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
        logger.info(f"Merchandise added: {item.name}")
        return {"message": "Merchandise added"}, 201

class MerchandiseItemV3(Resource):
    @jwt_required()
    def patch(self, id):
        user, err = require_admin()
        if err:
            return err
        item = Merchandise.query.get_or_404(id)
        data = request.get_json(silent=True) or {}
        for key in ["stock", "price"]:
            if key in data:
                setattr(item, key, data[key])
        db.session.commit()
        logger.info(f"Merchandise updated: {item.name}")
        return {"message": "Merchandise updated"}, 200

    @jwt_required()
    def delete(self, id):
        user, err = require_admin()
        if err:
            return err
        item = Merchandise.query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        logger.info(f"Merchandise deleted: {item.name}")
        return {"message": "Merchandise deleted"}, 200
