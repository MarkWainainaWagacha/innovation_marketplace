from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, db, ContactAudit
import os
from datetime import datetime
from functools import wraps
from marshmallow import Schema, fields, ValidationError
from tasks import send_email_task

CONTACT_LOG = {}
RATE_LIMIT_WINDOW = 60
MAX_EMAILS_PER_WINDOW = 3


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
def role_required(*roles):
    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user = User.query.get(get_jwt_identity())
            if not current_user or current_user.role not in roles:
                return make_response(message="Access denied", status="error", code=403)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# -----------------------------
# MARSHMALLOW SCHEMAS
# -----------------------------
class ContactSchema(Schema):
    subject = fields.Str(required=True)
    message = fields.Str(required=True)
    template_name = fields.Str(required=False)


# -----------------------------
# EMAIL TEMPLATE RENDER
# -----------------------------
def render_email_template(template_name: str, message: str):
    templates = {
        "welcome": f"<h1>Welcome</h1><p>{message}</p>",
        "alert": f"<strong>Alert:</strong> {message}",
        "promotion": f"<h3>Promotion!</h3><p>{message}</p>",
        "default": f"<p>{message}</p>"
    }
    return templates.get(template_name, templates["default"])


# -----------------------------
# USER LIST
# -----------------------------
class UserList(Resource):

    @role_required("admin", "recruiter")
    def get(self):
        current_user = User.query.get(get_jwt_identity())
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        search = request.args.get("search", "").strip()
        sort = request.args.get("sort", "id")
        include_inactive = request.args.get("include_inactive", "false").lower() == "true"
        role_filter = request.args.get("role", "").strip().lower()
        joined_after = request.args.get("joined_after", None)

        query = User.query
        if not include_inactive:
            query = query.filter(User.is_active == True)

        if search:
            query = query.filter(
                (User.first_name.ilike(f"%{search}%")) |
                (User.last_name.ilike(f"%{search}%")) |
                (User.email.ilike(f"%{search}%"))
            )

        if role_filter:
            query = query.filter(User.role == role_filter)

        if joined_after:
            try:
                date_obj = datetime.fromisoformat(joined_after)
                query = query.filter(User.created_at >= date_obj)
            except Exception:
                pass

        if hasattr(User, sort):
            query = query.order_by(getattr(User, sort))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        users = [
            {
                "id": u.id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email if current_user.role == "admin" else None,
                "is_active": u.is_active if current_user.role == "admin" else None,
                "role": u.role,
                "created_at": u.created_at.isoformat()
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

    @role_required("admin", "recruiter")
    def post(self, user_id: int):
        current_user = User.query.get(get_jwt_identity())
        user = User.query.get_or_404(user_id)

        if current_user.id == user_id:
            return make_response(message="Cannot contact yourself", status="error", code=400)
        if not user.is_active:
            return make_response(message="Cannot contact inactive user", status="error", code=400)

        now = datetime.utcnow().timestamp()
        timestamps = CONTACT_LOG.get(current_user.id, [])
        timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]

        if len(timestamps) >= MAX_EMAILS_PER_WINDOW:
            return make_response(message="Rate limit exceeded", status="error", code=429)
        timestamps.append(now)
        CONTACT_LOG[current_user.id] = timestamps

        try:
            data = ContactSchema().load(request.get_json() or {})
        except ValidationError as err:
            return make_response(message=str(err), status="error", code=400)

        recipient_email = (user.email or "").strip().lower()
        if not recipient_email:
            return make_response(message="User has no email", status="error", code=400)

        test_email = os.getenv("RESEND_TEST_EMAIL")
        to_emails = [test_email.strip().lower()] if test_email else [recipient_email]

        html_body = render_email_template(data.get("template_name"), data["message"])

        try:
            api_key = os.getenv("RESEND_API_KEY")
            from_email = os.getenv("RESEND_FROM")
            send_email_task.delay(payload={
                "from": from_email,
                "to": to_emails,
                "subject": data["subject"],
                "text": data["message"],
                "html": html_body
            }, api_key=api_key)
        except Exception as e:
            return make_response(message=f"Email queue failed: {e}", status="error", code=500)

        audit = ContactAudit(
            sender_id=current_user.id,
            recipient_id=user.id,
            recipient_email=recipient_email,
            subject=data["subject"],
            timestamp=datetime.utcnow()
        )
        db.session.add(audit)
        db.session.commit()

        # Analytics hook for dashboard consumption
        print(f"Analytics: user_contact_event sender={current_user.id} recipient={user.id} template={data.get('template_name')}")

        return make_response(message="Email queued successfully", data={"sent_to": len(to_emails)})


# -----------------------------
# CONTACT LOGS
# -----------------------------
class ContactLogs(Resource):

    @role_required("admin", "recruiter")
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
    @role_required("admin")
    def patch(self, user_id: int):
        user = User.query.get_or_404(user_id)
        user.is_active = False
        db.session.commit()
        return make_response(message="User deactivated")


class ReactivateUser(Resource):
    @role_required("admin")
    def patch(self, user_id: int):
        user = User.query.get_or_404(user_id)
        user.is_active = True
        db.session.commit()
        return make_response(message="User reactivated")


# -----------------------------
# USER ANALYTICS
# -----------------------------
class UserAnalytics(Resource):

    @role_required("admin")
    def get(self):
        total_users = User.query.count()
        active_users = User.query.filter(User.is_active == True).count()
        inactive_users = User.query.filter(User.is_active == False).count()
        contacts_sent = ContactAudit.query.count()
        contacts_today = ContactAudit.query.filter(
            ContactAudit.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).count()

        return make_response(data={
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "contacts_sent_total": contacts_sent,
            "contacts_sent_today": contacts_today
        }, message="Analytics summary")
