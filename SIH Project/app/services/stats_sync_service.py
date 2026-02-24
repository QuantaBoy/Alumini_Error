from datetime import datetime
from app.db import db
from app.services.leetcode_service import fetch_leetcode_user
from app.services.codeforces_service import fetch_codeforces_user
from app.services.codechef_service import fetch_codechef_user
from app.services.hackerrank_service import fetch_hackerrank_user

def sync_all_cp_stats(user):
    """
    Background worker to fetch all external CP platform stats.
    """
    if not user:
        return

    updated = False
    
    # 1. LeetCode
    if user.leetcode_username:
        print(f"Syncing LeetCode for {user.username}...")
        try:
            data = fetch_leetcode_user(user.leetcode_username)
            if data and "error" not in data:
                user.leetcode_data = data
                updated = True
                db.session.commit() # Save immediately
                try:
                    from app import socketio
                    socketio.emit("sync_complete", {"type": "stats_partial", "platform": "leetcode", "user_id": user.id})
                except Exception:
                    pass
        except Exception as e:
            print(f"LeetCode sync error for {user.username}: {e}")

    # 2. CodeForces
    if user.codeforces_username:
        print(f"Syncing CodeForces for {user.username}...")
        try:
            data = fetch_codeforces_user(user.codeforces_username)
            if data and "error" not in data:
                user.codeforces_data = data
                updated = True
                db.session.commit() # Save immediately
                try:
                    from app import socketio
                    socketio.emit("sync_complete", {"type": "stats_partial", "platform": "codeforces", "user_id": user.id})
                except Exception:
                    pass
        except Exception as e:
            print(f"CodeForces sync error for {user.username}: {e}")

    # 3. CodeChef
    if user.codechef_username:
        print(f"Syncing CodeChef for {user.username}...")
        try:
            data = fetch_codechef_user(user.codechef_username)
            if data and "error" not in data:
                user.codechef_data = data
                updated = True
                db.session.commit() # Save immediately
                try:
                    from app import socketio
                    socketio.emit("sync_complete", {"type": "stats_partial", "platform": "codechef", "user_id": user.id})
                except Exception:
                    pass
        except Exception as e:
            print(f"CodeChef sync error for {user.username}: {e}")

    # 4. HackerRank
    if user.hackerrank_username:
        print(f"Syncing HackerRank for {user.username}...")
        try:
            data = fetch_hackerrank_user(user.hackerrank_username)
            if data and "error" not in data:
                user.hackerrank_data = data
                updated = True
                db.session.commit() # Save immediately
                try:
                    from app import socketio
                    socketio.emit("sync_complete", {"type": "stats_partial", "platform": "hackerrank", "user_id": user.id})
                except Exception:
                    pass
        except Exception as e:
            print(f"HackerRank sync error for {user.username}: {e}")

    # Always update sync timestamp to prevent infinite loops on page load
    user.last_stats_sync = datetime.utcnow()
    db.session.commit()

    if updated:
        print(f"All CP stats updated for {user.username}")
        # 🔔 Notify client via SocketIO
        from app import socketio
        socketio.emit("sync_complete", {"type": "stats", "user_id": user.id})
    else:
        print(f"Sync attempt finished for {user.username} (no changes)")
        # Still notify to stop any loading spinners
        from app import socketio
        socketio.emit("sync_complete", {"type": "stats_no_change", "user_id": user.id})
