import os
from flask import Flask, jsonify
from sqlalchemy import text

from server.config import config_by_name
from server.extensions import db, jwt, bcrypt, cors


def create_app(config_name: str = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)

    # Configure CORS to accept requests from frontends
    origins = app.config.get("CORS_ORIGINS", "*")
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
            }
        },
        supports_credentials=True,
    )

    from server.routes.auth import auth_bp
    from server.routes.documents import documents_bp
    from server.routes.export import export_bp
    from server.routes.templates import templates_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(templates_bp)

    register_error_handlers(app)

    @app.get("/api/health")
    def health():
        # Check database connectivity
        db_status = "connected"
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"error: {str(e)}"

        return jsonify({
            "status": "ok",
            "message": "LegalEase Backend API & Database are running smoothly.",
            "database": {
                "status": db_status,
                "engine": app.config.get("SQLALCHEMY_DATABASE_URI", "").split(":")[0] or "sqlite"
            },
            "version": "1.0.0"
        }), 200

    with app.app_context():
        db.create_all()
        # Safe migration for sqlite
        try:
            if db.engine.dialect.name == "sqlite":
                with db.engine.connect() as conn:
                    result = conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()
                    existing_cols = [row[1] for row in result]
                    if "role" not in existing_cols:
                        conn.exec_driver_sql("ALTER TABLE users ADD COLUMN role VARCHAR(32) DEFAULT 'user'")
                    if "updated_at" not in existing_cols:
                        conn.exec_driver_sql("ALTER TABLE users ADD COLUMN updated_at DATETIME")
        except Exception:
            pass

    return app


def register_error_handlers(app: Flask):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error."}), 500