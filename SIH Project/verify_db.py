from app import app_run, db
from app.models import User, Post

app = app_run()
with app.app_context():
    user_count = User.query.count()
    post_count = Post.query.count()
    print(f"User count: {user_count}")
    print(f"Post count: {post_count}")
    
    if user_count == 0 and post_count == 0:
        print("VERIFICATION SUCCESS: Database is clean.")
    else:
        print("VERIFICATION FAILED: Database is not empty.")
