from datetime import datetime
from app.db import db
from app.models import LinkedinProfile
from app.services.linkedin_scraper import LinkedInProScraper
from dataclasses import asdict

def sync_linkedin_for_user(user):
    """
    Syncs the user's LinkedIn profile data using the scraper.
    """
    if not user or not user.linkedin_url:
        return

    # Update status to pending
    try:
        user.linkedin_sync_status = "pending"
        db.session.commit()
    except Exception as e:
        print(f"Error setting LinkedIn pending status: {e}")

    scraper = None
    try:
        # Initialize scraper
        # Assuming no proxy for now, or use environment variables if needed
        scraper = LinkedInProScraper(use_proxy=False)
        
        # Scrape the profile
        print(f"Scraping LinkedIn profile for user {user.username} ({user.linkedin_url})...")
        profile_data = scraper.scrape_full_profile(user.linkedin_url)
        
        if not profile_data:
            raise Exception("No data returned from LinkedIn scraper")

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
            
            # Structured data
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
        print(f"LinkedIn sync successful for {user.username}")
        
    except Exception as e:
        print(f"LinkedIn sync failed for {user.username}: {e}")
        user.linkedin_sync_status = "failed"
        db.session.commit()
    finally:
        if scraper:
            try:
                scraper.close()
            except Exception:
                pass
