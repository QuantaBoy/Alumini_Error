from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager
from .config import Config
from .db import db
from .models import User   # ← import model here
from app.scheduler import scheduler, sync_all_users
import os

socketio = SocketIO(cors_allowed_origins="*")
login_manager = LoginManager()

def app_run():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # ✅ USER LOADER DEFINED HERE (NO CIRCULAR IMPORT)
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------------- SCHEDULER ----------------
    scheduler.init_app(app)

    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        scheduler.add_job(
            id="github_auto_sync",
            func=lambda: sync_all_users(app),  # ✅ PASS APP
            trigger="interval",
            hours=6,
        replace_existing=True
    )
    scheduler.start()


    # ---------------- ROUTES ----------------
    from .routes.home import home_bp
    from .routes.message_routes import message_bp
    from .routes.auth import auth_bp
    from .routes.subscription import subscription_bp
    from .routes.leetcode_routes import leetcode_bp
    from .routes.profile import profile_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(message_bp, url_prefix="/message")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(subscription_bp, url_prefix="/subscription")
    app.register_blueprint(leetcode_bp, url_prefix="/leetcode")
    app.register_blueprint(profile_bp, url_prefix="/profile")

    with app.app_context():
        db.create_all()

    return app
