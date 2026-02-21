from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Post, User
from app.db import db
from sqlalchemy.orm.attributes import flag_modified
import os
from datetime import datetime

home_bp = Blueprint("home", __name__)

# Correct path: go up from routes/home.py -> routes -> app -> static/uploads
# __file__ = app/routes/home.py
# dir(__file__) = app/routes
# dir(dir(__file__)) = app
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@home_bp.route("/")
@login_required
def home():
    return render_template("Home.html", user=current_user)

@home_bp.route("/chat", methods=["GET", "POST"])
def chat():
    username = request.args.get("username") or request.form.get("username")
    if not username:
        return redirect(url_for("home.home"))
    return render_template("chat_interface.html", username=username)

# ========== POST ROUTES ==========

@home_bp.route("/api/posts", methods=["GET"])
@login_required
def get_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    # Debugging: Print posts to console
    post_list = [p.to_dict() for p in posts]
    for p in post_list:
        print(f"DEBUG POST: ID={p['_id']}, Content='{p['content']}', Media={len(p['media'])} items")
    return jsonify(post_list)

@home_bp.route("/api/posts", methods=["POST"])
@login_required
def create_post():
    content = request.form.get("content", "").strip()
    files = request.files.getlist("files")

    if not content and not files:
        return jsonify({"message": "Post content or media required"}), 400

    media = []

    for f in files:
        if f.filename:
            filename = secure_filename(f.filename)
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            f.save(save_path)

            media.append({
                "url": f"/static/uploads/{filename}",
                "type": "video" if f.content_type and f.content_type.startswith("video") else "image"
            })

    post = Post(
        content=content,
        user_id=current_user.id,
        media=media if media else [],
        likes=[],
        comments=[]
    )

    db.session.add(post)
    db.session.commit()

    return jsonify(post.to_dict()), 201

@home_bp.route("/api/posts/<int:post_id>", methods=["PUT"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        return jsonify({"message": "Not authorized"}), 401
    
    data = request.get_json()
    post.content = data.get("content", post.content)
    
    db.session.commit()
    return jsonify(post.to_dict())

@home_bp.route("/api/posts/<int:post_id>", methods=["DELETE"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        return jsonify({"message": "Not authorized"}), 401
    
    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Post deleted"})

@home_bp.route("/api/posts/<int:post_id>/like", methods=["PUT"])
@login_required
def toggle_like(post_id):
    post = Post.query.get_or_404(post_id)
    
    likes = list(post.likes or [])
    user_id_str = str(current_user.id)
    
    likes = [str(like) for like in likes]
    
    if user_id_str in likes:
        likes.remove(user_id_str)
    else:
        likes.append(user_id_str)
    
    post.likes = likes
    flag_modified(post, "likes")  # Tell SQLAlchemy JSON column was mutated
    db.session.commit()
    
    return jsonify({"likes": len(likes)})

@home_bp.route("/api/posts/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    
    data = request.get_json()
    text = data.get("text", "").strip()
    
    if not text:
        return jsonify({"message": "Comment required"}), 400
    
    comments = list(post.comments or [])
    comments.append({
        "user_id": str(current_user.id),
        "username": current_user.username,
        "text": text,
        "created_at": datetime.utcnow().isoformat()
    })
    
    post.comments = comments
    flag_modified(post, "comments")  # Tell SQLAlchemy JSON column was mutated
    db.session.commit()
    
    return jsonify(post.comments), 201


@home_bp.route("/api/upload-cover", methods=["POST"])
@login_required
def upload_cover():
    """Upload a cover photo for the profile page."""
    if 'cover' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files['cover']
    if not f or not f.filename:
        return jsonify({"error": "Empty file"}), 400

    allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
    if ext not in allowed:
        return jsonify({"error": "Invalid file type"}), 400

    covers_folder = os.path.join(UPLOAD_FOLDER, "covers")
    os.makedirs(covers_folder, exist_ok=True)

    filename = secure_filename(f"cover_{current_user.id}.{ext}")
    save_path = os.path.join(covers_folder, filename)
    f.save(save_path)

    cover_url = f"/static/uploads/covers/{filename}"

    # Store on user model (reuse portfolio_url slot or add a dedicated column)
    # We'll store in a JSON encoded string in admin_code temporarily until a migration adds cover_photo
    # Better: store in user.admin_code only if not set — instead store via a session-safe approach
    # Use a simple file convention: cover_{user_id}.ext — client just reads this URL
    return jsonify({"url": cover_url}), 200


@home_bp.route("/api/upload-avatar", methods=["POST"])
@login_required
def upload_avatar():
    """Upload a profile avatar photo."""
    if 'avatar' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files['avatar']
    if not f or not f.filename:
        return jsonify({"error": "Empty file"}), 400

    allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
    if ext not in allowed:
        return jsonify({"error": "Invalid file type"}), 400

    avatars_folder = os.path.join(UPLOAD_FOLDER, "avatars")
    os.makedirs(avatars_folder, exist_ok=True)

    filename = secure_filename(f"avatar_{current_user.id}.{ext}")
    save_path = os.path.join(avatars_folder, filename)
    f.save(save_path)

    avatar_url = f"/static/uploads/avatars/{filename}"
    return jsonify({"url": avatar_url}), 200

