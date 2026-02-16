from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, db, ContactAudit
import os
import requests
import time
from datetime import datetime
from threading import Thread
from functools import wraps
from marshmallow import Schema, fields, ValidationError

RESEND_API_URL = "https://api.resend.com/emails"
CONTACT_LOG = {}
RATE_LIMIT_WINDOW = 60
MAX_EMAILS_PER_WINDOW = 3
EMAIL_RETRY_LIMIT = 3
EMAIL_RETRY_DELAY = 5  # seconds


# -----------------------------
# CENTRALIZED RESPONSE
# -----------------------------
def make_response(data=None, message="", status="success", code=200):
    return jsonify({
        "status": status,
        "message": message,
        "data": data or {}
    }), code


# -----------------------------
# ROLE-BASED DECORATOR
# -----------------------------
def admin_required(func):
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user = User.query.get(get_jwt_identity())
        if not current_user or not current_user.is_admin:
            return make_response(message="Admin access required", status="error", code=403)
        return func(*args, **kwargs)
    return wrapper


# -----------------------------
# MARSHMALLOW SCHEMAS
# -----------------------------
class ContactSchema(Schema):
    subject = fields.Str(required=True)
    message = fields.Str(required=True)


# -----------------------------
# BACKGROUND EMAIL SENDER WITH RETRY
# -----------------------------
def send_email_with_retry(payload, api_key, retry_count=0):
    try:
        r = requests.post(
            RESEND_API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=20
        )
        if r.status_code >= 400:
            raise Exception(f"HTTP {r.status_code}")
    except Exception as e:
        if retry_count < EMAIL_RETRY_LIMIT:
            time.sleep(EMAIL_RETRY_DELAY)
            send_email_with_retry(payload, api_key, retry_count + 1)
        else:
            print(f"Failed to send email after {EMAIL_RETRY_LIMIT} retries: {e}")


def send_email_async(payload, api_key):
    Thread(target=send_email_with_retry, args=(payload, api_key)).start()


# -----------------------------
# USER LIST
# -----------------------------
class UserList(Resource):

    @jwt_required()
    def get(self):
        current_user = User.query.get(get_jwt_identity())
        if not current_user:
            return make_response(message="User not found", status="error", code=404)

        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        search = request.args.get("search", "").strip()
        sort = request.args.get("sort", "id")
        include_inactive = request.args.get("include_inactive", "false").lower() == "true"

        query = User.query
        if not include_inactive or not current_user.is_admin:
            query = query.filter(User.is_active == True)

        if search:
            query = query.filter(
                (User.first_name.ilike(f"%{search}%")) |
                (User.last_name.ilike(f"%{search}%")) |
                (User.email.ilike(f"%{search}%"))
            )

        if hasattr(User, sort):
            query = query.order_by(getattr(User, sort))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        users = [
            {
                "id": u.id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email if current_user.is_admin else None,
                "is_active": u.is_active if current_user.is_admin else None
            }
            for u in pagination.items
        ]

        return make_response(data={
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page,
            "users": users
        })


# -----------------------------
# USER CONTACT
# -----------------------------
class UserContact(Resource):

    @admin_required
    def post(self, user_id: int):
        current_user = User.query.get(get_jwt_identity())
        user = User.query.get_or_404(user_id)

        if current_user.id == user_id:
            return make_response(message="Cannot contact yourself", status="error", code=400)
        if not user.is_active:
            return make_response(message="Cannot contact inactive user", status="error", code=400)

        # Rate limiting
        now = time.time()
        timestamps = CONTACT_LOG.get(current_user.id, [])
        timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]

        if len(timestamps) >= MAX_EMAILS_PER_WINDOW:
            return make_response(message="Rate limit exceeded", status="error", code=429)
        timestamps.append(now)
        CONTACT_LOG[current_user.id] = timestamps

        # Validate input
        try:
            data = ContactSchema().load(request.get_json() or {})
        except ValidationError as err:
            return make_response(message=str(err), status="error", code=400)

        recipient_email = (user.email or "").strip().lower()
        if not recipient_email:
            return make_response(message="User has no email", status="error", code=400)

        test_email = os.getenv("RESEND_TEST_EMAIL")
        to_emails = [test_email.strip().lower()] if test_email else [recipient_email]

        try:
            api_key = os.getenv("RESEND_API_KEY")
            from_email = os.getenv("RESEND_FROM")
        except Exception as e:
            return make_response(message=f"Email service not configured: {e}", status="error", code=500)

        payload = {
            "from": from_email,
            "to": to_emails,
            "subject": data["subject"],
            "text": data["message"],
            "html": f"<p>{data['message']}</p>"
        }

        send_email_async(payload, api_key)

        # Log to database
        audit = ContactAudit(
            sender_id=current_user.id,
            recipient_id=user.id,
            recipient_email=recipient_email,
            subject=data["subject"],
            timestamp=datetime.utcnow()
        )
        db.session.add(audit)
        db.session.commit()

        return make_response(message="Email queued successfully", data={"sent_to": len(to_emails)})


# -----------------------------
# CONTACT LOGS
# -----------------------------
class ContactLogs(Resource):

    @admin_required
    def get(self):
        audits = ContactAudit.query.order_by(ContactAudit.timestamp.desc()).all()
        logs = [
            {
                "sender_id": a.sender_id,
                "recipient_id": a.recipient_id,
                "recipient_email": a.recipient_email,
                "subject": a.subject,
                "timestamp": a.timestamp.isoformat()
            } for a in audits
        ]
        return make_response(data={"total_logs": len(logs), "logs": logs})


# -----------------------------
# DEACTIVATE / REACTIVATE USER
# -----------------------------
class DeactivateUser(Resource):
    @admin_required
    def patch(self, user_id: int):
        user = User.query.get_or_404(user_id)
        user.is_active = False
        db.session.commit()
        return make_response(message="User deactivated")


class ReactivateUser(Resource):
    @admin_required
    def patch(self, user_id: int):
        user = User.query.get_or_404(user_id)
        user.is_active = True
        db.session.commit()
        return make_response(message="User reactivated")
