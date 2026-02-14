import logging
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Merchandise, User, OrderMerchandise

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("merchandise_v1")

def require_admin():
    raw_id = get_jwt_identity()
    try:
        user_id = int(raw_id)
    except (TypeError, ValueError):
        return None, ({"error": "Invalid token identity"}, 401)
    user = User.query.get(user_id)
    if not user or not user.role or user.role.name != "admin":
        return None, ({"error": "Admin access required"}, 403)
    return user, None

def float_price(p):
    try:
        return float(p)
    except (TypeError, ValueError):
        return 0.0

class MerchandiseList(Resource):
    def get(self):
        items = Merchandise.query.all()
        return [
            {
                "id": m.id,
                "name": m.name,
                "description": m.description,
                "price": float_price(m.price),
                "stock": m.stock,
                "image_url": m.image_url
            } for m in items
        ], 200

    @jwt_required()
    def post(self):
        user, err = require_admin()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        item = Merchandise(
            name=str(data.get("name")).strip(),
            description=(data.get("description") or "").strip(),
            price=data.get("price"),
            stock=data.get("stock"),
            image_url=(data.get("image_url") or "").strip()
        )
        db.session.add(item)
        db.session.commit()
        logger.info(f"Merchandise added: {item.name}")
        return {"message": "Merchandise added"}, 201

class MerchandiseItem(Resource):
    @jwt_required()
    def patch(self, id):
        user, err = require_admin()
        if err:
            return err
        item = Merchandise.query.get_or_404(id)
        data = request.get_json(silent=True) or {}
        for key in ["name", "description", "price", "stock", "image_url"]:
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
        OrderMerchandise.query.filter_by(merchandise_id=item.id).delete(synchronize_session=False)
        db.session.delete(item)
        db.session.commit()
        logger.info(f"Merchandise deleted: {item.name}")
        return {"message": "Merchandise deleted"}, 200
