from datetime import datetime, timedelta
from app.db import db
from app.models import GithubProfile
from app.services.github_service import build_full_github_profile

SYNC_INTERVAL = timedelta(hours=6)

def sync_github_for_user(user):
    if not user or not user.github_username:
        return

    # DEBUG: Always run sync for now
    # if user.last_github_sync:
    #     if datetime.utcnow() - user.last_github_sync < SYNC_INTERVAL:
    #         return

    # Set Pending Status
    try:
        user.github_sync_status = "pending"
        db.session.commit()
        with open("debug_sync.txt", "a") as f:
            f.write(f"Started sync for {user.username}\n")
    except Exception as e:
        with open("debug_sync.txt", "a") as f:
            f.write(f"DB Error setting pending: {str(e)}\n")

    try:
        data = build_full_github_profile(user.github_username)

        gp = data["github_profile"]

        snapshot = GithubProfile(
            user_id=user.id,
            github_username=gp["username"],
            name=gp["name"],
            bio=gp["bio"],
            followers=gp["followers"],
            following=gp["following"],
            account_age_days=gp["account_age_days"],
            profile_url=gp["profile_url"],
            activity_summary=data["activity_summary"],
            language_intelligence=data["language_intelligence"],
            developer_score=data["developer_score"],
            repo_quality=data["repo_quality"]
        )

        db.session.add(snapshot)
        user.last_github_sync = datetime.utcnow()
        user.github_sync_status = "success"
        db.session.commit()

    except Exception as e:
        user.github_sync_status = "failed"
        db.session.commit()
        print("GitHub sync failed:", e)
