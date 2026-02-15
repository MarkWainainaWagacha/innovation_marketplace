from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_restful import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db

from resources.mpesa import MpesaPay, MpesaCallback
from resources.auth import Signup, Login, UpdateProfile
from resources.projects import ProjectList, ProjectDetail, ProjectContactTeam
from resources.merchandise import MerchandiseList, MerchandiseItem
from resources.orders import OrderCreate, OrderDelete
from resources.admin import CategoryCreate, ApproveProject, RejectProject, AdminUserList
from resources.recruiters import BrowseProjects
from resources.likes import ProjectLikeToggle
from resources.users import UserList, UserContact


def create_app():
    app = Flask(__name__)

    # Configuration
    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        database_url or
        "postgresql+psycopg2://biboko:12345678@localhost:5432/moringa_innovation_marketplace_db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)

    # CORS
    CORS(app, supports_credentials=True, origins=[
        "http://localhost:3000",
        "http://localhost:3001"
    ])

    # Initialize API
    api = Api(app)

    # Register resources

    # Auth
    api.add_resource(Signup, "/signup")
    api.add_resource(Login, "/login")
    api.add_resource(UpdateProfile, "/profile")

    # Projects
    api.add_resource(ProjectList, "/projects")
    api.add_resource(ProjectDetail, "/projects/<int:project_id>")
    api.add_resource(ProjectContactTeam, "/projects/<int:project_id>/contact")
    api.add_resource(ProjectLikeToggle, "/projects/<int:project_id>/like")

    # Merchandise
    api.add_resource(MerchandiseList, "/merchandise")
    api.add_resource(MerchandiseItem, "/merchandise/<int:id>")

    # Orders
    api.add_resource(OrderCreate, "/orders")
    api.add_resource(OrderDelete, "/orders/<int:order_id>")

    # Admin
    api.add_resource(CategoryCreate, "/admin/categories")
    api.add_resource(ApproveProject, "/admin/projects/<int:project_id>/approve")
    api.add_resource(RejectProject, "/admin/projects/<int:project_id>/reject")
    api.add_resource(AdminUserList, "/admin/users")

    # Users
    api.add_resource(UserList, "/users")
    api.add_resource(UserContact, "/users/<int:user_id>/contact")

    # Recruiters
    api.add_resource(BrowseProjects, "/recruiters/projects")

    # Mpesa
    api.add_resource(MpesaPay, "/mpesa/pay")
    api.add_resource(MpesaCallback, "/mpesa/callback")

    @app.route("/")
    def home():
        return {"status": "API running"}, 200

    # ✅ Request logging middleware
    @app.before_request
    def log_request_info():
        ip = request.remote_addr
        method = request.method
        path = request.path
        app.logger.info(f"Request from {ip}: {method} {path}")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5555, debug=True)
