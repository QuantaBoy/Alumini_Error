from datetime import datetime
from app.db import db
from app.models import LinkedinProfile
from dataclasses import asdict

def sync_linkedin_for_user(user):
    """
    Syncs the user's LinkedIn profile data using the scraper.
    Adds robust error logging to `debug_sync.txt` and emits a socket event on failure.
    """
    if not user or not user.linkedin_url:
        return

    # Update status to pending
    try:
        user.linkedin_sync_status = "pending"
        db.session.commit()
    except Exception as e:
        _log_debug(f"Error setting LinkedIn pending status for user {getattr(user, 'id', 'unknown')}: {e}")

    scraper = None
    try:
        # Import scraper lazily so missing deps raise at instantiation time
        from app.services.linkedin_scraper import LinkedInProScraper

        # Initialize scraper
        scraper = LinkedInProScraper(use_proxy=False)

        # Scrape the profile
        _log_debug(f"Scraping LinkedIn profile for user {user.username} ({user.linkedin_url})...")
        profile_data = scraper.scrape_full_profile(user.linkedin_url)

        if not profile_data or not profile_data.fullName:
            raise Exception("LinkedIn scraper could not extract profile name. Possibly blocked or profile hidden.")

        # Convert dataclass to dict
        data = asdict(profile_data)

        # Create LinkedinProfile entry (snapshot)
        linkedin_profile = LinkedinProfile(
            user_id=user.id,
            linkedin_url=data.get('linkedinUrl') or user.linkedin_url,
            full_name=data.get('fullName'),
            headline=data.get('headline'),
            about=data.get('about'),
            location=data.get('location'),
            connections=data.get('connections'),
            followers=data.get('followers'),
            experience=data.get('experiences', []),
            education=data.get('educations', []),
            projects=data.get('projects', []),
            skills=data.get('skills', []),
            languages=data.get('languages', []),
            certifications=data.get('certifications', []),
            posts=data.get('posts', [])
        )

        # Add to DB
        db.session.add(linkedin_profile)

        # Update User status
        user.last_linkedin_sync = datetime.utcnow()
        user.linkedin_sync_status = "success"
        db.session.commit()
        _log_debug(f"LinkedIn sync successful for {user.username} (id={user.id})")

        # 🔔 Notify client via SocketIO
        from app import socketio
        try:
            socketio.emit("sync_complete", {"type": "linkedin", "user_id": user.id})
        except Exception as se:
            _log_debug(f"Socket emit failed for user {user.id}: {se}")

    except Exception as e:
        import traceback as _tb
        err = _tb.format_exc()
        _log_debug(f"LinkedIn sync failed for user {getattr(user, 'username', 'unknown')} (id={getattr(user, 'id', 'unknown')}): {e}\n{err}")
        try:
            user.linkedin_sync_status = "failed"
            db.session.commit()
        except Exception as ce:
            _log_debug(f"Failed to set linkedin_sync_status for user {getattr(user, 'id', 'unknown')}: {ce}")
        # Try to notify clients about failure as well
        try:
            from app import socketio
            socketio.emit("sync_complete", {"type": "linkedin_failed", "user_id": user.id})
        except Exception:
            pass
    finally:
        if scraper:
            try:
                # Attempt to gracefully close scraper if provided
                if hasattr(scraper, 'close'):
                    scraper.close()
            except Exception as e:
                _log_debug(f"Error closing scraper for user {getattr(user, 'id', 'unknown')}: {e}")


def _log_debug(msg: str):
    """Append a timestamped message to debug_sync.txt for troubleshooting."""
    try:
        from datetime import datetime as _dt
        with open("debug_sync.txt", "a", encoding="utf-8") as f:
            f.write(f"[{_dt.utcnow().isoformat()}] {msg}\n")
    except Exception:
        # If logging fails, fall back to printing so the server log has some info
        print(msg)
