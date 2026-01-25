from flask import Blueprint, render_template_string
from app.models import User
from app import db
import os
from flask import current_app

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users')
def user_stats():
    from datetime import datetime, timedelta
    from sqlalchemy.exc import OperationalError
    from sqlalchemy import text
    
    try:
        # Try to query users with last_seen
        users = User.query.all()
        # Access last_seen on the first user to trigger error if column missing
        if users:
            _ = users[0].last_seen
            
    except OperationalError as e:
        if "no such column: users.last_seen" in str(e) or "has no column named last_seen" in str(e):
            # Auto-migrate
            try:
                if 'sqlite' in str(db.engine.url):
                    db.session.execute(text("ALTER TABLE users ADD COLUMN last_seen DATETIME"))
                else:
                    # Generic SQL, works for Postgres/MySQL usually too
                    db.session.execute(text("ALTER TABLE users ADD COLUMN last_seen TIMESTAMP"))
                db.session.commit()
                # Retry query
                users = User.query.all()
            except Exception as migration_error:
                return f"<h1>Migration Error</h1><p>{str(migration_error)}</p>"
        else:
            raise e

    count = len(users)
    
    # Calculate active users (active in last 5 minutes)
    five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
    active_users = [u for u in users if u.last_seen and u.last_seen > five_mins_ago]
    active_count = len(active_users)
    
    html = f"""
    <html>
    <head>
        <title>User Admin</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .status-success {{ color: green; font-weight: bold; }}
            .status-failed {{ color: red; font-weight: bold; }}
            .status-pending {{ color: orange; font-weight: bold; }}
            .btn {{ padding: 5px 10px; background: #dc2626; color: white; text-decoration: none; border-radius: 4px; }}
            .active-badge {{ background: #22c55e; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h1>User Database Audit</h1>
            <a href="/" style="padding: 10px; background: #eee; text-decoration: none; border-radius: 5px;">Back to Home</a>
        </div>
        
        <div style="margin-bottom: 20px; padding: 15px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;">
            <h2 style="margin: 0; color: #166534;">Active Users: {active_count}</h2>
            <p style="margin: 5px 0 0 0; color: #15803d;">(Users active in the last 5 minutes)</p>
        </div>
        
        <p><strong>Total Registered Users:</strong> {count}</p>
        <table>
            <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>GitHub</th>
                <th>Sync Status</th>
                <th>Last Seen</th>
            </tr>
    """
    
    for u in users:
        sync_class = f"status-{u.github_sync_status}" if u.github_sync_status else ""
        
        # Determine online status
        is_online = u.last_seen and u.last_seen > five_mins_ago
        status_badge = '<span class="active-badge">ONLINE</span>' if is_online else ''
        
        last_seen_str = u.last_seen.strftime("%Y-%m-%d %H:%M:%S") if u.last_seen else "Never"
        
        html += f"""
            <tr>
                <td>{u.id}</td>
                <td>{u.username}</td>
                <td>{u.email}</td>
                <td>{u.role}</td>
                <td>{status_badge} {'✅' if u.profile_completed else '❌'}</td>
                <td>{u.github_username or '-'}</td>
                <td class="{sync_class}">{u.github_sync_status or 'Not Started'}</td>
                <td>{last_seen_str}</td>
            </tr>
        """
        
    html += """
        </table>
        <br>
        <hr>
        <h3>Danger Zone</h3>
        <p>
            <a href='/admin/reset-db-force' class="btn" onclick="return confirm('⚠️ WARNING: This will delete ALL users, posts, and data. Are you sure?');">
                ☢️ WIPE DATABASE (Reset All)
            </a>
        </p>
    </body>
    </html>
    """
    return render_template_string(html)

@admin_bp.route("/reset-db-force")
def reset_db_force():
    from flask_login import logout_user
    from sqlalchemy import text
    
    try:
        logout_user()
        
        # Attempt 1: Physical File Deletion
        db.session.remove()
        db.engine.dispose()
        
        paths = [
            os.path.join(current_app.instance_path, 'app.db'),
            os.path.join(os.getcwd(), 'app.db')
        ]
        
        deleted = []
        failed_deletes = []
        
        for p in paths:
            if os.path.exists(p):
                try:
                    os.remove(p)
                    deleted.append(f"Deleted {p}")
                except Exception as e:
                    failed_deletes.append(f"Lock on {p}")

        # Attempt 2: SQL Truncate (Fallback if file locked)
        if failed_deletes:
            try:
                # Disable FK checks to allow deletion
                if 'sqlite' in str(db.engine.url):
                    db.session.execute(text("PRAGMA foreign_keys = OFF"))
                
                # Delete all rows from known tables
                db.session.execute(text("DELETE FROM posts"))
                db.session.execute(text("DELETE FROM github_profiles"))
                db.session.execute(text("DELETE FROM users"))
                
                db.session.commit()
                deleted.append("Executed SQL DELETE on all tables")
            except Exception as e:
                deleted.append(f"SQL Delete Failed: {e}")

        # Re-ensure structure
        db.create_all()
        
        from app.models import User
        count = User.query.count()
        
        return f"<h1>Reset Complete</h1><p>{'; '.join(deleted)}</p><p><b>Remaining Users: {count}</b> (Should be 0)</p><p><a href='/'>Home</a></p>"
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>"
