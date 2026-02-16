from dotenv import load_dotenv
load_dotenv()

import os
import time
import signal
import sys
import uuid
import logging
from flask import Flask, request, jsonify, g
from flask_migrate import Migrate
from flask_restful import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
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

    # --------------------------------------------------
    # Configuration
    # --------------------------------------------------
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
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB limit

    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])

    # --------------------------------------------------
    # Logging Configuration
    # --------------------------------------------------
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    # --------------------------------------------------
    # Initialize Extensions
    # --------------------------------------------------
    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)

    # --------------------------------------------------
    # CORS Configuration
    # --------------------------------------------------
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        allowed_origins = os.getenv("PROD_FRONTEND_URLS", "").split(",")
    else:
        allowed_origins = ["http://localhost:3000", "http://localhost:3001"]

    CORS(app, supports_credentials=True, origins=allowed_origins)

    # --------------------------------------------------
    # API Initialization
    # --------------------------------------------------
    api = Api(app)

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

    # --------------------------------------------------
    # Health Endpoint
    # --------------------------------------------------
    app.start_time = time.time()
    app.endpoint_times = {}

    @app.route("/health", methods=["GET"])
    def health_check():
        uptime = time.time() - app.start_time
        avg_durations = {
            k: round(sum(v) / len(v), 3)
            for k, v in app.endpoint_times.items()
        }
        return jsonify({
            "status": "ok",
            "uptime_seconds": round(uptime, 2),
            "environment": env,
            "avg_request_durations": avg_durations
        })

    @app.route("/")
    def home():
        return {"status": "API running"}, 200

    # --------------------------------------------------
    # Middleware
    # --------------------------------------------------

    # Generate Request ID
    @app.before_request
    def generate_request_id():
        g.request_id = str(uuid.uuid4())
        g.start_time = time.time()

    # Validate JSON
    @app.before_request
    def validate_json_body():
        if request.method in ["POST", "PUT"] and request.path not in ["/", "/health"]:
            if not request.is_json:
                return jsonify({"error": "Request body must be JSON"}), 400

    # API Key Check
    @app.before_request
    def check_api_key():
        if request.path in ["/", "/health", "/token/refresh"]:
            return
        api_key = request.headers.get("X-API-KEY")
        valid_key = os.getenv("API_KEY", "dev-key")
        if api_key != valid_key:
            return jsonify({"error": "Invalid API key"}), 401

    # Rate Limiting
    request_times = {}

    @app.before_request
    def rate_limit():
        if request.path in ["/", "/health"]:
            return
        ip = request.remote_addr
        now = time.time()
        window = 60
        max_requests = 30

        times = request_times.get(ip, [])
        times = [t for t in times if now - t < window]

        if len(times) >= max_requests:
            return jsonify({"error": "Too many requests"}), 429

        times.append(now)
        request_times[ip] = times

    # Logging After Request
    @app.after_request
    def log_request(response):
        duration = time.time() - g.start_time
        path = request.path

        if path not in app.endpoint_times:
            app.endpoint_times[path] = []
        app.endpoint_times[path].append(duration)

        response.headers["X-Request-ID"] = g.request_id

        app.logger.info(
            f"RID={g.request_id} | "
            f"{request.remote_addr} {request.method} {path} "
            f"{response.status_code} | {duration:.3f}s"
        )

        return response

    # JWT Refresh
    @app.route("/token/refresh", methods=["POST"])
    @jwt_required(refresh=True)
    def refresh_token():
        identity = get_jwt_identity()
        new_token = create_access_token(identity=identity)
        return {"access_token": new_token}, 200

    # Global Error Handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        code = getattr(e, "code", 500)
        message = getattr(e, "description", str(e))
        return jsonify({
            "error": message,
            "status_code": code,
            "request_id": g.get("request_id")
        }), code

    # Graceful Shutdown
    def shutdown_signal_handler(signum, frame):
        app.logger.info(f"Shutting down gracefully (signal {signum})...")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_signal_handler)
    signal.signal(signal.SIGTERM, shutdown_signal_handler)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5555, debug=True)
