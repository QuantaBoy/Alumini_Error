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

    codechef_data = None
    if user.codechef_username:
        try:
            from app.services.codechef_service import fetch_codechef_user
            codechef_data = fetch_codechef_user(user.codechef_username)
        except Exception as e:
            print(f"Error fetching CodeChef data: {e}")

    codeforces_data = None
    if user.codeforces_username:
        try:
            from app.services.codeforces_service import fetch_codeforces_user
            codeforces_data = fetch_codeforces_user(user.codeforces_username)
        except Exception as e:
            print(f"Error fetching CodeForces data: {e}")

    leetcode_data = None
    if user.leetcode_username:
        try:
            from app.services.leetcode_service import fetch_leetcode_user
            leetcode_data = fetch_leetcode_user(user.leetcode_username)
        except Exception as e:
             print(f"Error fetching LeetCode data: {e}")

    # --- POST ANALYTICS CALCULATION ---
    post_analytics = {
        "likes": 0,
        "comments": 0,
        "shares": 0,
        "impressions": 0,
        "reach": 0,
        "engagement_rate": 0
    }

    if linkedin and linkedin.posts:
        posts = linkedin.posts if isinstance(linkedin.posts, list) else []
        for post in posts:
            stats = post.get("stats", {})
            post_analytics["likes"] += stats.get("like", 0)
            post_analytics["comments"] += stats.get("comments", 0)
            post_analytics["shares"] += stats.get("reposts", 0)
        
        # Estimate Impressions & Reach (as scraper doesn't get these private metrics)
        interactions = post_analytics["likes"] + post_analytics["comments"] + post_analytics["shares"]
        if interactions > 0:
            post_analytics["impressions"] = interactions * 20 # Rough multiplier
            post_analytics["reach"] = int(post_analytics["impressions"] * 0.65)
            post_analytics["engagement_rate"] = round((interactions / post_analytics["impressions"]) * 100, 1)
    # --- SKILLS / LANGUAGE ANALYSIS ---
    skills_data = {}
    if github and github.language_intelligence:
        lang_stats = github.language_intelligence
        
        # 1. Calculate raw percentages based on Repo Count (or you could use 'stars' or 'active_days')
        # Using repo count as proxy for familiarity
        total_repos_count = sum(item.get("repos", 0) for item in lang_stats.values())
        
        raw_skills = {}
        if total_repos_count > 0:
            for lang, data in lang_stats.items():
                # Filter out configuration/markup languages often considered "noise" if desired,
                # but broadly relying on the "above average" rule requested by user.
                repos_count = data.get("repos", 0)
                percent = (repos_count / total_repos_count) * 100
                raw_skills[lang] = percent

        # 2. Calculate Average Percentage
        if raw_skills:
            avg_percent = sum(raw_skills.values()) / len(raw_skills)
            
            # 3. Filter: Only keep skills > Average
            # We also ensure we keep at least the top 1 if everything is flat, though average check handles most.
            filtered_skills = {k: v for k, v in raw_skills.items() if v >= avg_percent}
            
            # If strictly filtering removes too much (e.g. all equal), revert to all or top 5
            if not filtered_skills:
                filtered_skills = dict(sorted(raw_skills.items(), key=lambda x: x[1], reverse=True)[:5])
            
            # 4. Sort Descending
            skills_data = dict(sorted(filtered_skills.items(), key=lambda item: item[1], reverse=True))
            
            # Round for display
            skills_data = {k: round(v, 1) for k, v in skills_data.items()}

    # --- SKILLS CHART PRE-CALCULATION ---
    skills_gradient = "conic-gradient(#e0e0e0 0deg 360deg)" # Default gray
    skills_legend = []
    
    if skills_data:
        colors = ['#4caf50', '#2196f3', '#ff9800', '#9c27b0', '#f44336']
        gradient_parts = []
        current_deg = 0
        
        for i, (lang, percent) in enumerate(skills_data.items()):
            color = colors[i % len(colors)]
            start_deg = current_deg
            end_deg = current_deg + (percent * 3.6)
            
            # CSS Conic Gradient Syntax: color start_deg end_deg
            gradient_parts.append(f"{color} {start_deg}deg {end_deg}deg")
            
            skills_legend.append({
                "lang": lang,
                "percent": percent,
                "color": color
            })
            
            current_deg = end_deg
            
        if gradient_parts:
            skills_gradient = f"conic-gradient({', '.join(gradient_parts)})"

    response = make_response(render_template(
        "profile.html",
        user=user,
        github=github,
        linkedin=linkedin,
        leetcode=leetcode_data,
        codeforces=codeforces_data,
        codechef=codechef_data,
        hackerrank=None,
        analytics=post_analytics,
        skills_data=skills_data,
        skills_gradient=skills_gradient,
        skills_legend=skills_legend
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

    # Allow users to edit their profile even if completed
    # if user.profile_completed:
    #     return redirect(url_for("home.home"))

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
        user.leetcode_username = request.form.get("leetcode_username")
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
