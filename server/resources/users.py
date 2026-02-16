from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
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
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return {"status": "error", "message": "User not found"}, 404

        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        search = request.args.get("search", "").strip()
        sort = request.args.get("sort", "id")

        query = User.query

        # Search
        if search:
            query = query.filter(
                (User.first_name.ilike(f"%{search}%")) |
                (User.last_name.ilike(f"%{search}%")) |
                (User.email.ilike(f"%{search}%"))
            )

        # Sorting
        if hasattr(User, sort):
            query = query.order_by(getattr(User, sort))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "status": "success",
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page,
            "users": [
                {
                    "id": u.id,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                    # Only admin sees emails
                    "email": u.email if current_user.is_admin else None,
                }
                for u in pagination.items
            ],
        }, 200


class UserContact(Resource):
    """
    POST /users/<user_id>/contact
    - JWT required
    - Prevent self-contact
    - Only admins can contact any user
    """

    @jwt_required()
    def post(self, user_id: int):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return {"status": "error", "message": "User not found"}, 404

        if current_user_id == user_id:
            return {"status": "error", "message": "You cannot contact yourself"}, 400

        # Only admin can contact any user
        if not current_user.is_admin:
            return {"status": "error", "message": "Only admins can contact users"}, 403

        user = User.query.get_or_404(user_id)

        data = request.get_json() or {}
        subject = (data.get("subject") or "").strip()
        message = (data.get("message") or "").strip()

        if not subject or not message:
            return {"status": "error", "message": "Subject and message are required"}, 400

        recipient = (user.email or "").strip().lower()
        if not recipient:
            return {"status": "error", "message": "This user has no email"}, 400

        test_email = os.getenv("RESEND_TEST_EMAIL")
        to_emails = [test_email.strip().lower()] if test_email else [recipient]

        try:
            api_key = _require_env("RESEND_API_KEY")
            from_email = _require_env("RESEND_FROM")
        except Exception as e:
            return {
                "status": "error",
                "message": "Email service not configured",
                "details": str(e),
            }, 500

        payload = {
            "from": from_email,
            "to": to_emails,
            "subject": subject,
            "text": message,
            "html": f"<p>{message}</p>",
        }

        try:
            r = requests.post(
                RESEND_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=20,
            )
        except requests.RequestException as e:
            return {
                "status": "error",
                "message": "Failed to connect to email service",
                "details": str(e),
            }, 502

        if r.status_code >= 400:
            try:
                detail = r.json()
            except Exception:
                detail = {"message": r.text}

            return {
                "status": "error",
                "message": "Failed to send email",
                "details": detail,
            }, 502

        return {
            "status": "success",
            "message": "Email sent successfully",
            "sent_to": len(to_emails),
        }, 200
