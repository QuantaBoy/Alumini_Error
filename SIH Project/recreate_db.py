from app import app_run, db

app = app_run()
with app.app_context():
    db.create_all()
    print("Database tables recreated successfully.")
