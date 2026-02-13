from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, User, Project, Category

# -------------------------
# Helper functions
# -------------------------

def require_admin():
    """
    Ensures the JWT identity matches a real user and that the user is an admin.

    Returns:
        Tuple:
            - User instance if valid admin
            - None and an error dict with status code if invalid
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        # Invalid token
        return None, ({"error": "Invalid token user. Please log in again."}, 401)

    if not user.role or user.role.name != "admin":
        # Not an admin
        return None, ({"error": "Admin access required"}, 403)

    return user, None


# -------------------------
# Category Resource
# -------------------------

class CategoryCreate(Resource):
    """Admin-only endpoint to create a new category"""

    @jwt_required()
    def post(self):
        """
        Creates a category with a unique name.
        Expects JSON: { "name": str, "description": str }
        """
        # Check admin privileges
        user, err = require_admin()
        if err:
            return err

        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()

        if not name:
            return {"error": "Missing category name"}, 400

        # Prevent duplicates
        if Category.query.filter_by(name=name).first():
            return {"error": "Category already exists"}, 400

        category = Category(
            name=name,
            description=(data.get("description") or "").strip()
        )

        db.session.add(category)
        db.session.commit()

        return {"message": f"Category '{category.name}' created"}, 201


# -------------------------
# Project Approval Resources
# -------------------------

class ApproveProject(Resource):
    """Admin-only endpoint to approve a project"""

    @jwt_required()
    def post(self, project_id: int):
        """
        Approves a project.
        Expects JSON: { "reason": str }
        """
        user, err = require_admin()
        if err:
            return err

        project = Project.query.get(project_id)
        if not project:
            return {"error": "Project not found"}, 404

        data = request.get_json(silent=True) or {}
        reason = (data.get("reason") or "").strip()

        project.status = "approved"
        project.approval_reason = reason
        db.session.commit()

        return {
            "message": f"Project '{project.title}' approved",
            "reason": reason
        }, 200


class RejectProject(Resource):
    """Admin-only endpoint to reject a project"""

    @jwt_required()
    def post(self, project_id: int):
        """
        Rejects a project.
        Expects JSON: { "reason": str }
        """
        user, err = require_admin()
        if err:
            return err

        project = Project.query.get(project_id)
        if not project:
            return {"error": "Project not found"}, 404

        data = request.get_json(silent=True) or {}
        reason = (data.get("reason") or "").strip()

        project.status = "rejected"
        project.rejection_reason = reason
        db.session.commit()

        return {
            "message": f"Project '{project.title}' rejected",
            "reason": reason
        }, 200


# -------------------------
# Admin User List Resource
# -------------------------

class AdminUserList(Resource):
    """Admin-only endpoint to list all users"""

    @jwt_required()
    def get(self):
        """
        Returns a list of all users with roles, status, and creation timestamp
        """
        user, err = require_admin()
        if err:
            return err

        users = User.query.all()

        return [
            {
                "id": u.id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
                "role": u.role.name if u.role else None,
                "status": u.status,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ], 200

# -------------------------
# End of server/admin.py
# -------------------------
