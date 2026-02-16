from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, db
import os
import requests
import time
from datetime import datetime

RESEND_API_URL = "https://api.resend.com/emails"

CONTACT_LOG = {}
CONTACT_AUDIT = []

RATE_LIMIT_WINDOW = 60
MAX_EMAILS_PER_WINDOW = 3


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


# -----------------------------
# USER LIST
# -----------------------------
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
        include_inactive = request.args.get("include_inactive", "false").lower() == "true"

        query = User.query

        # Show only active users unless admin explicitly asks
        if not include_inactive or not current_user.is_admin:
            query = query.filter(User.is_active == True)

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
                    "email": u.email if current_user.is_admin else None,
                    "is_active": u.is_active if current_user.is_admin else None,
                }
                for u in pagination.items
            ],
        }, 200


# -----------------------------
# CONTACT USER
# -----------------------------
class UserContact(Resource):

    @jwt_required()
    def post(self, user_id: int):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return {"status": "error", "message": "User not found"}, 404

        if current_user_id == user_id:
            return {"status": "error", "message": "You cannot contact yourself"}, 400

        if not current_user.is_admin:
            return {"status": "error", "message": "Only admins can contact users"}, 403

        user = User.query.get_or_404(user_id)

        if not user.is_active:
            return {"status": "error", "message": "Cannot contact inactive user"}, 400

        # Rate limiting
        now = time.time()
        timestamps = CONTACT_LOG.get(current_user_id, [])
        timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]

        if len(timestamps) >= MAX_EMAILS_PER_WINDOW:
            return {"status": "error", "message": "Rate limit exceeded"}, 429

        timestamps.append(now)
        CONTACT_LOG[current_user_id] = timestamps

        data = request.get_json() or {}
        subject = (data.get("subject") or "").strip()
        message = (data.get("message") or "").strip()

        if not subject or not message:
            return {"status": "error", "message": "Subject and message required"}, 400

        recipient = (user.email or "").strip().lower()
        if not recipient:
            return {"status": "error", "message": "User has no email"}, 400

        test_email = os.getenv("RESEND_TEST_EMAIL")
        to_emails = [test_email.strip().lower()] if test_email else [recipient]

        try:
            api_key = _require_env("RESEND_API_KEY")
            from_email = _require_env("RESEND_FROM")
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

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
            return {"status": "error", "message": str(e)}, 502

        if r.status_code >= 400:
            return {"status": "error", "message": "Email failed"}, 502

        CONTACT_AUDIT.append({
            "sender_id": current_user_id,
            "recipient_id": user_id,
            "recipient_email": recipient,
            "subject": subject,
            "timestamp": datetime.utcnow().isoformat()
        })

        return {"status": "success", "message": "Email sent"}, 200


# -----------------------------
# ADMIN: VIEW CONTACT LOGS
# -----------------------------
class ContactLogs(Resource):

    @jwt_required()
    def get(self):
        current_user = User.query.get(get_jwt_identity())

        if not current_user or not current_user.is_admin:
            return {"status": "error", "message": "Admin access required"}, 403

        return {
            "status": "success",
            "total_logs": len(CONTACT_AUDIT),
            "logs": CONTACT_AUDIT
        }, 200


# -----------------------------
# ADMIN: SOFT DELETE USER
# -----------------------------
class DeactivateUser(Resource):

    @jwt_required()
    def patch(self, user_id: int):
        current_user = User.query.get(get_jwt_identity())

        if not current_user or not current_user.is_admin:
            return {"status": "error", "message": "Admin access required"}, 403

        user = User.query.get_or_404(user_id)
        user.is_active = False
        db.session.commit()

        return {"status": "success", "message": "User deactivated"}, 200


# -----------------------------
# ADMIN: REACTIVATE USER
# -----------------------------
class ReactivateUser(Resource):

    @jwt_required()
    def patch(self, user_id: int):
        current_user = User.query.get(get_jwt_identity())

        if not current_user or not current_user.is_admin:
            return {"status": "error", "message": "Admin access required"}, 403

        user = User.query.get_or_404(user_id)
        user.is_active = True
        db.session.commit()

        return {"status": "success", "message": "User reactivated"}, 200
