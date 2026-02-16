from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from models import User
import os
import requests

RESEND_API_URL = "https://api.resend.com/emails"


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


class UserList(Resource):
    @jwt_required()
    def get(self):
        search = request.args.get("search", "").strip()
        query = User.query

        if search:
            query = query.filter(
                (User.first_name.ilike(f"%{search}%")) |
                (User.last_name.ilike(f"%{search}%")) |
                (User.email.ilike(f"%{search}%"))
            )

        users = query.all()

        return [
            {
                "id": u.id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
            }
            for u in users
        ], 200


class UserContact(Resource):
    def post(self, user_id: int):
        user = User.query.get_or_404(user_id)
        data = request.get_json() or {}
        subject = data.get("subject", "").strip()
        message = data.get("message", "").strip()

        if not subject or not message:
            return {"error": "Subject and message required"}, 400

        try:
            api_key = _require_env("RESEND_API_KEY")
            from_email = _require_env("RESEND_FROM")
        except Exception as e:
            return {"error": str(e)}, 500

        payload = {
            "from": from_email,
            "to": [user.email],
            "subject": subject,
            "text": message,
        }

        r = requests.post(
            RESEND_API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=20,
        )

        if r.status_code >= 400:
            return {"error": "Email failed"}, 502

        return {"ok": True}, 200
