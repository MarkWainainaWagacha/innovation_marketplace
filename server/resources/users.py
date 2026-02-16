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
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))

        pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "users": [
                {
                    "id": u.id,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                    "email": u.email,
                }
                for u in pagination.items
            ],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page,
        }, 200


class UserContact(Resource):
    def post(self, user_id: int):
        user = User.query.get_or_404(user_id)

        data = request.get_json() or {}
        subject = (data.get("subject") or "").strip()
        message = (data.get("message") or "").strip()

        if not subject or not message:
            return {"error": "Subject and message are required"}, 400

        recipient = (user.email or "").strip().lower()
        if not recipient:
            return {"error": "This user has no email"}, 400

        test_email = os.getenv("RESEND_TEST_EMAIL")
        to_emails = [test_email.strip().lower()] if test_email else [recipient]

        try:
            api_key = _require_env("RESEND_API_KEY")
            from_email = _require_env("RESEND_FROM")
        except Exception as e:
            return {"error": "Email service not configured", "details": str(e)}, 500

        payload = {
            "from": from_email,
            "to": to_emails,
            "subject": subject,
            "text": message,
        }

        r = requests.post(
            RESEND_API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=20,
        )

        if r.status_code >= 400:
            try:
                detail = r.json()
            except Exception:
                detail = {"message": r.text}
