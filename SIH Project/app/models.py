from .db import db
from sqlalchemy.dialects.sqlite import JSON
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    profile_completed = db.Column(db.Boolean, default=False)
    github_username = db.Column(db.String(120), index=True)

    leetcode_username = db.Column(db.String(120))
    codeforces_username = db.Column(db.String(120))
    codechef_username = db.Column(db.String(120))
    hackerrank_username = db.Column(db.String(120))

    linkedin_url = db.Column(db.String(255))
    portfolio_url = db.Column(db.String(255))

    last_github_sync = db.Column(db.DateTime)
    github_sync_status = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Role management
    role = db.Column(db.String(20), default="student") # student, alumni, management
    student_id = db.Column(db.String(50))
    graduation_year = db.Column(db.String(10))
    admin_code = db.Column(db.String(50))

    github_profiles = db.relationship(
        "GithubProfile",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

class GithubProfile(db.Model):
    __tablename__ = "github_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    synced_at = db.Column(db.DateTime, default=datetime.utcnow)

    github_username = db.Column(db.String(120))
    name = db.Column(db.String(120))
    bio = db.Column(db.Text)
    followers = db.Column(db.Integer)
    following = db.Column(db.Integer)
    account_age_days = db.Column(db.Integer)
    profile_url = db.Column(db.String(255))

    activity_summary = db.Column(JSON)
    language_intelligence = db.Column(JSON)
    developer_score = db.Column(JSON)
    repo_quality = db.Column(JSON)

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, default="")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    media = db.Column(JSON)   # [{url, type}]
    likes = db.Column(JSON, default=lambda: [])  # List of user IDs who liked
    comments = db.Column(JSON, default=lambda: [])  # [{user_id, text, created_at}]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        from flask_login import current_user
        user = User.query.get(self.user_id)
        
        # safely handle likes list
        likes_list = self.likes or []
        likes_count = len(likes_list)
        
        # check if current user liked
        is_liked = False
        if current_user.is_authenticated:
            is_liked = str(current_user.id) in [str(l) for l in likes_list]

        return {
            "_id": self.id,
            "content": self.content,
            "media": self.media or [],
            "likes": likes_list,
            "likeCount": likes_count,
            "isLiked": is_liked,
            "comments": self.comments or [],
            "commentCount": len(self.comments or []),
            "createdAt": self.created_at.isoformat() + "Z",
            "username": user.username if user else "Unknown",
            "author_pfp": "/static/images/avatar_3d.png" # Placeholder/default for now
        }
