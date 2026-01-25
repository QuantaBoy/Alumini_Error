from flask_apscheduler import APScheduler
from app.models import User
from app.services.github_sync_service import sync_github_for_user

scheduler = APScheduler()

def sync_all_users(app):
    """
    Runs GitHub sync inside Flask app context
    """
    print("⏱️ GitHub auto-sync running...")

    with app.app_context():
        users = User.query.filter(
            User.github_username.isnot(None)
        ).all()

        for user in users:
            sync_github_for_user(user)
