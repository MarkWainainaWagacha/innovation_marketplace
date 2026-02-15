from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask
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


def configure_app(app):
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


def register_resources(api):
    api.add_resource(Signup, "/signup")
    api.add_resource(Login, "/login")
    api.add_resource(UpdateProfile, "/profile")
    api.add_resource(ProjectList, "/projects")
    api.add_resource(ProjectDetail, "/projects/<int:project_id>")
    api.add_resource(ProjectContactTeam, "/projects/<int:project_id>/contact")
    api.add_resource(ProjectLikeToggle, "/projects/<int:project_id>/like")
    api.add_resource(MerchandiseList, "/merchandise")
    api.add_resource(MerchandiseItem, "/merchandise/<int:id>")
    api.add_resource(OrderCreate, "/orders")
    api.add_resource(OrderDelete, "/orders/<int:order_id>")
    api.add_resource(CategoryCreate, "/admin/categories")
    api.add_resource(ApproveProject, "/admin/projects/<int:project_id>/approve")
    api.add_resource(RejectProject, "/admin/projects/<int:project_id>/reject")
    api.add_resource(AdminUserList, "/admin/users")
    api.add_resource(UserList, "/users")
    api.add_resource(UserContact, "/users/<int:user_id>/contact")
    api.add_resource(BrowseProjects, "/recruiters/projects")
    api.add_resource(MpesaPay, "/mpesa/pay")
    api.add_resource(MpesaCallback, "/mpesa/callback")


def create_app():
    app = Flask(__name__)
    configure_app(app)

    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)

    CORS(app, supports_credentials=True, origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")])

    api = Api(app)
    register_resources(api)

    @app.route("/")
    def home():
        return {"status": "API running"}, 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5555, debug=True)
