from flask import Blueprint, render_template, request, redirect, url_for, make_response
from flask_login import login_required, current_user
from app.models import GithubProfile, User
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

    response = make_response(render_template(
        "profile.html",
        user=user,
        github=github,
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

        # 🚀 Trigger GitHub sync ONCE
        if user.github_username:
            sync_github_for_user(user)

        return redirect(url_for("profile.profile_page"))

    return render_template("complete_profile.html")
