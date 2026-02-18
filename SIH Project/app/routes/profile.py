from flask import Blueprint, render_template, request, redirect, url_for, make_response
from flask_login import login_required, current_user
from app.models import GithubProfile, LinkedinProfile, User
from app.db import db
from app.services.github_sync_service import sync_github_for_user

profile_bp = Blueprint("profile", __name__)

# =========================
# PROFILE PAGE
# =========================
@profile_bp.route("/")
@login_required
def profile_page():
    user = current_user

    if not user.profile_completed:
        return redirect(url_for("profile.complete_profile"))

    github = (
        GithubProfile.query
        .filter_by(user_id=user.id)
        .order_by(GithubProfile.synced_at.desc())
        .first()
    )

    # 🔥 SORT PROJECTS (repos) FOR UI ONLY
    if github and github.repo_quality:
        github.repo_quality = sorted(
            github.repo_quality,
            key=lambda r: (
                r.get("stars", 0),
                -r.get("last_push_days_ago", 9999)
            ),
            reverse=True
        )

    linkedin = (
        LinkedinProfile.query
        .filter_by(user_id=user.id)
        .order_by(LinkedinProfile.synced_at.desc())
        .first()
    )

    response = make_response(render_template(
        "profile.html",
        user=user,
        github=github,
        linkedin=linkedin,
        leetcode=None,
        codeforces=None,
        codechef=None,
        hackerrank=None
    ))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# =========================
# COMPLETE PROFILE
# =========================
@profile_bp.route("/complete-profile", methods=["GET", "POST"])
@login_required
def complete_profile():
    user = current_user

    if user.profile_completed:
        return redirect(url_for("home.home"))

    if request.method == "POST":
        github_username = request.form.get("github_username", "").strip()

        # 🔒 Prevent duplicate GitHub username
        if github_username:
            existing = User.query.filter(
                User.github_username == github_username,
                User.id != user.id
            ).first()

            if existing:
                return "GitHub username already linked to another account", 400

        user.github_username = github_username or None
        user.linkedin_url = request.form.get("linkedin_url")
        user.codeforces_username = request.form.get("codeforces_username")
        user.codechef_username = request.form.get("codechef_username")
        user.hackerrank_username = request.form.get("hackerrank_username")
        user.portfolio_url = request.form.get("portfolio_url")
        user.profile_completed = True

        db.session.commit()

        # 🚀 Trigger GitHub sync in BACKGROUND
        if user.github_username:
            import threading
            from flask import current_app
            
            # Capture real app object to pass to thread
            real_app = current_app._get_current_object()

            def bg_sync(app_obj, u_id):
                with app_obj.app_context():
                    from app.models import User
                    # Re-query user to avoid session issues
                    u = User.query.get(u_id)
                    if u:
                        print(f"Starting background sync for user {u.id}...")
                        sync_github_for_user(u)
                        print(f"Background sync finished. Status: {u.github_sync_status}")
                    
            thread = threading.Thread(target=bg_sync, args=(real_app, user.id))
            thread.start()

        # 🔗 Trigger LinkedIn sync in BACKGROUND
        if user.linkedin_url:
            import threading
            from flask import current_app
            
            # Capture real app object to pass to thread
            real_app_li = current_app._get_current_object()

            def bg_sync_linkedin(app_obj, u_id):
                with app_obj.app_context():
                    from app.models import User
                    from app.services.linkedin_sync_service import sync_linkedin_for_user
                    # Re-query user to avoid session issues
                    u = User.query.get(u_id)
                    if u:
                        print(f"Starting background LinkedIn sync for user {u.id}...")
                        try:
                            sync_linkedin_for_user(u)
                        except Exception as e:
                            print(f"Error calling sync service: {e}")
                        print(f"Background LinkedIn sync finished. Status: {u.linkedin_sync_status}")
                    
            linkedin_thread = threading.Thread(target=bg_sync_linkedin, args=(real_app_li, user.id))
            linkedin_thread.start()

        return redirect(url_for("profile.profile_page"))

    return render_template("complete_profile.html")


# =========================
# RESYNC LINKEDIN
# =========================
@profile_bp.route("/resync-linkedin")
@login_required
def resync_linkedin():
    user = current_user
    if not user.linkedin_url:
        return redirect(url_for("profile.profile_page"))

    # Reset status
    user.linkedin_sync_status = "pending"
    db.session.commit()

    # Trigger Thread
    import threading
    from flask import current_app
    
    real_app_li = current_app._get_current_object()

    def bg_sync_linkedin(app_obj, u_id):
        with app_obj.app_context():
            from app.models import User
            from app.services.linkedin_sync_service import sync_linkedin_for_user
            u = User.query.get(u_id)
            if u:
                print(f"Starting background LinkedIn RESYNC for user {u.id}...")
                try:
                    sync_linkedin_for_user(u)
                except Exception as e:
                     print(f"Error calling sync service: {e}")
                print(f"Background LinkedIn sync finished. Status: {u.linkedin_sync_status}")
    
    linkedin_thread = threading.Thread(target=bg_sync_linkedin, args=(real_app_li, user.id))
    linkedin_thread.start()

    return redirect(url_for("profile.profile_page"))
