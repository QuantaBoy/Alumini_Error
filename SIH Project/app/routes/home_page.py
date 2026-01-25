from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Post
from app.db import db
import os

home_bp = Blueprint("home", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@home_bp.route("/")
@login_required
def home():
    return render_template("Home.html")

@home_bp.route("/api/posts", methods=["GET"])
@login_required
def get_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return jsonify([p.to_dict() for p in posts])

@home_bp.route("/api/posts", methods=["POST"])
@login_required
def create_post():
    content = request.form.get("content", "").strip()
    files = request.files.getlist("files")

    if not content and not files:
        return jsonify({"message": "Post content or media required"}), 400

    media = []

    for f in files:
        filename = secure_filename(f.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        f.save(save_path)

        media.append({
            "url": f"/uploads/{filename}",
            "type": "video" if f.mimetype.startswith("video") else "image"
        })

    post = Post(
        content=content,
        user_id=current_user.id,
        media=media
    )

    db.session.add(post)
    db.session.commit()

    return jsonify(post.to_dict()), 201
