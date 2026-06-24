"""
app/__init__.py
===============
Flask application factory.
Creates the app, registers extensions, and registers all blueprints.
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# ── Extensions (initialised without app for factory pattern) ──────────────────
db            = SQLAlchemy()
login_manager = LoginManager()
migrate       = Migrate()


def create_app(config_name: str | None = None) -> Flask:
    """
    Application factory.

    Args:
        config_name: 'development' | 'production' | None (→ reads FLASK_ENV).

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ── Load configuration ────────────────────────────────────────────────────
    from .config import config_map
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    # ── Initialise extensions ─────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view     = "auth.login"
    login_manager.login_message  = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # ── User loader (required by Flask-Login) ─────────────────────────────────
    from .models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    # ── Register blueprints ───────────────────────────────────────────────────
    from .auth.routes      import auth_bp
    from .dashboard.routes import dashboard_bp
    from .devices.routes   import devices_bp
    from .monitor.routes   import monitor_bp
    from .alerts.routes    import alerts_bp
    from .reports.routes   import reports_bp

    app.register_blueprint(auth_bp,      url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/")
    app.register_blueprint(devices_bp,   url_prefix="/devices")
    app.register_blueprint(monitor_bp,   url_prefix="/monitor")
    app.register_blueprint(alerts_bp,    url_prefix="/alerts")
    app.register_blueprint(reports_bp,   url_prefix="/reports")

    # ── Create DB tables + seed default admin ─────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_default_admin(app)

    return app


def _seed_default_admin(app: Flask) -> None:
    """Insert the default admin user if the users table is empty."""
    from .models import User

    if User.query.count() == 0:
        admin = User(
            username = app.config["ADMIN_USERNAME"],
            email    = app.config["ADMIN_EMAIL"],
            role     = "admin",
        )
        admin.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()
        print(f"[SEED] Default admin created: {admin.username}")
