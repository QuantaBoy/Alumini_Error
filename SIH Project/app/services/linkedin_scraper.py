import time
import json
import random
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
import os
import pickle

# Ensure undetected_chromedriver is installed
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError as e:
    print("CRITICAL ERROR: specific libraries are missing.")
    print(f"Details: {e}")
    print("Please run: pip install undetected-chromedriver selenium beautifulsoup4")
    exit(1)

# ------------------------------------------------------------------------------
# Rich Data Structures (Matching Apify-style Output)
# ------------------------------------------------------------------------------

@dataclass
class Date:
    date: str = ""
    relative: str = ""
    timestamp: Optional[int] = None

@dataclass
class Media:
    type: str = ""
    url: str = ""
    images: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Author:
    first_name: str = ""
    last_name: str = ""
    headline: str = ""
    username: str = ""
    profile_url: str = ""
    profile_picture: str = ""

@dataclass
class PostStats:
    total_reactions: int = 0
    like: int = 0
    comments: int = 0
    reposts: int = 0

@dataclass
class Post:
    text: str = ""
    posted_at: Date = field(default_factory=Date)
    url: str = ""
    author: Author = field(default_factory=Author)
    stats: PostStats = field(default_factory=PostStats)
    media: Optional[Media] = None

@dataclass
class Experience:
    title: str = ""
    companyName: str = ""
    employmentType: str = ""
    location: str = ""
    startDate: str = ""
    endDate: str = ""
    description: str = ""

@dataclass
class Education:
    schoolName: str = ""
    degreeName: str = ""
    fieldOfStudy: str = ""
    startDate: str = ""
    endDate: str = ""
    grade: str = ""
    activities: str = ""

@dataclass
class Skill:
    name: str = ""
    endorsements: int = 0

@dataclass
class Certification:
    name: str = ""
    issuingOrganization: str = ""
    issueDate: str = ""
    expirationDate: str = ""
    credentialUrl: str = ""

@dataclass
class Project:
    title: str = ""
    description: str = ""
    startDate: str = ""
    endDate: str = ""
    url: str = ""

@dataclass
class Language:
    name: str = ""
    proficiency: str = ""

@dataclass
class Profile:
    linkedinUrl: str = ""
    fullName: str = ""
    headline: str = ""
    location: str = ""
    about: str = ""
    connections: str = ""
    followers: str = ""
    profilePic: str = ""
    
    # Contact Info
    email: str = ""
    phone: str = ""
    website: str = ""
    
    experiences: List[Experience] = field(default_factory=list)
    educations: List[Education] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)
    
    # New Sections
    certifications: List[Certification] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    languages: List[Language] = field(default_factory=list)
    
    posts: List[Post] = field(default_factory=list)

# ------------------------------------------------------------------------------
# Pro Scraper Class
# ------------------------------------------------------------------------------

class LinkedInProScraper:
    def __init__(self, use_proxy=False, proxy_string=None):
        self.driver = self._setup_driver(use_proxy, proxy_string)

    def _setup_driver(self, use_proxy, proxy_string):
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        # HEADLESS MODE (Invisible) - Commented out for visual verification
        # options.add_argument("--headless=new") 
        # options.add_argument("--window-size=1920,1080")

        if use_proxy and proxy_string:
            print(f"Configuring Proxy: {proxy_string}")
            options.add_argument(f'--proxy-server={proxy_string}')

        try:
            driver = uc.Chrome(options=options, use_subprocess=True)
            return driver
        except Exception as e:
            print(f"Failed to start Undetected Chrome: {e}")
            raise e

    # --------------------------------------------------------------------------
    # Human Simulation
    # --------------------------------------------------------------------------

    def _human_delay(self, min_seconds=2, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def _simulate_human_scroll(self):
        """Standard human-like scrolling down the page."""
        # In headless, sometimes body height extraction can be tricky, but this generally works.
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        current_position = self.driver.execute_script("return window.pageYOffset")
        
        while current_position < total_height:
            scroll_step = random.randint(300, 600) 
            current_position += scroll_step
            self.driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.5, 1.2))
            
            # Occasional pause/scroll up
            if random.random() < 0.15:
                current_position -= random.randint(50, 150)
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(1.0, 2.0))
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height > total_height:
                total_height = new_height
            if current_position >= total_height:
                break

    def _clean_text(self, text: Optional[str]) -> str:
        if not text: return ""
        return " ".join(text.split()).strip()

    # --------------------------------------------------------------------------
    # Session
    # --------------------------------------------------------------------------

    def login_and_save_cookies(self):
        print("Checking session state...")
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(3)

        if os.path.exists("linkedin_cookies.pkl"):
            print("Loading cookies...")
            cookies = pickle.load(open("linkedin_cookies.pkl", "rb"))
            for cookie in cookies:
                try: self.driver.add_cookie(cookie)
                except: pass
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(5)
        
        if "feed" in self.driver.current_url:
            print("Logged in!")
            return

        print("\n" + "="*50)
        print("ACTION REQUIRED: Log in manually to LinkedIn.")
        print("="*50 + "\n")
        
        while "feed" not in self.driver.current_url:
            time.sleep(1)
        
        print("Login detected! Saving cookies...")
        pickle.dump(self.driver.get_cookies(), open("linkedin_cookies.pkl", "wb"))

    # --------------------------------------------------------------------------
    # Detailed Extraction Logic
    # --------------------------------------------------------------------------

    def get_contact_info(self, profile):
        try:
            # Click "Contact Info" button
            # Usually id="top-card-text-details-contact-info"
            contact_btn = self.driver.find_element(By.ID, "top-card-text-details-contact-info")
            if contact_btn:
                contact_btn.click()
                self._human_delay(2,3)
                
                # Wait for modal
                modal = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "pv-contact-info__content"))
                )
                soup = BeautifulSoup(modal.get_attribute("outerHTML"), "html.parser")
                
                # Email
                email_section = soup.find("section", class_="ci-email")
                if email_section:
                    link = email_section.find("a")
                    if link: profile.email = self._clean_text(link.text)
                
                # Phone
                phone_section = soup.find("section", class_="ci-phone")
                if phone_section:
                    nums = phone_section.find_all("span")
                    for n in nums:
                         txt = self._clean_text(n.text)
                         if any(c.isdigit() for c in txt): 
                             profile.phone = txt
                             break
                
                # Website
                web_section = soup.find("section", class_="ci-websites")
                if web_section:
                    link = web_section.find("a")
                    if link: profile.website = link.get("href", "")

                # Close modal
                close_btn = self.driver.find_element(By.CLASS_NAME, "artdeco-modal__dismiss")
                if close_btn: close_btn.click()
                self._human_delay(1,2)
        except:
            pass

    def get_profile_main(self, url: str) -> Profile:
        print(f"Navigating to Profile: {url}")
        self.driver.get(url)
        self._human_delay(3, 5)
        self._simulate_human_scroll() # Read the whole page to trigger lazy loading
        
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        profile = Profile(linkedinUrl=url)

        # Basic Info
        try:
            name_tag = soup.find("h1", class_="text-heading-xlarge")
            profile.fullName = self._clean_text(name_tag.text) if name_tag else ""

            headline_tag = soup.find("div", class_="text-body-medium")
            profile.headline = self._clean_text(headline_tag.text) if headline_tag else ""

            loc_tag = soup.find("span", class_="text-body-small inline t-black--light break-words")
            profile.location = self._clean_text(loc_tag.text) if loc_tag else ""
            
            about_section = soup.find("section", {"id": "about"})
            if about_section:
                 # Often inside a hidden span if expanded, or just span
                 about_div = about_section.find_next("div", class_="display-flex ph5 pv3")
                 if about_div:
                     about_text = about_div.find("span", class_="visually-hidden") or about_div.find("span")
                     profile.about = self._clean_text(about_text.text) if about_text else ""
            
            # Profile Pic (High Quality from img tag)
            img_tag = soup.find("img", class_="pv-top-card-profile-picture__image")
            if img_tag and img_tag.has_attr("src"):
                profile.profilePic = img_tag["src"]

        except Exception as e:
            print(f"Error extracting main info: {e}")
        
        # Try to get Contact Info (Email/Phone) if possible
        self.get_contact_info(profile)
        
        return profile

    def get_generic_section(self, profile_url, section_name, dataclass_type, target_list):
        """Helper to scrape generic list pages like /details/certifications/"""
        url = f"{profile_url.rstrip('/')}/details/{section_name}/"
        print(f"Getting {section_name.capitalize()}: {url}")
        self.driver.get(url)
        self._human_delay(3, 5)
        self._simulate_human_scroll()
        
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        items = soup.find_all("li", class_="pvs-list__paged-list-item")
        
        for item in items:
            obj = dataclass_type()
            try:
                texts = [self._clean_text(t.text) for t in item.find_all("span", class_="visually-hidden")]
                texts = [t for t in texts if t]
                
                # Heuristics based on order
                if dataclass_type == Certification:
                    if len(texts) >= 1: obj.name = texts[0]
                    if len(texts) >= 2: obj.issuingOrganization = texts[1]
                    if len(texts) >= 3: obj.issueDate = texts[2]
                
                elif dataclass_type == Project:
                    if len(texts) >= 1: obj.title = texts[0]
                    if len(texts) >= 2: obj.startDate = texts[1] # e.g. "Jan 2023 - Present"
                    # Description is harder to pinpoint, taking rest as generic text
                
                elif dataclass_type == Language:
                    if len(texts) >= 1: obj.name = texts[0]
                    if len(texts) >= 2: obj.proficiency = texts[1]

                # Append if we found at least a name/title
                if getattr(obj, "name", None) or getattr(obj, "title", None):
                    target_list.append(obj)
            except: pass

    def get_experience(self, profile_url, profile):
        # Visit dedicated page: /details/experience/
        url = f"{profile_url.rstrip('/')}/details/experience/"
        print(f"Getting Experience: {url}")
        self.driver.get(url)
        self._human_delay(3, 5)
        self._simulate_human_scroll()
        
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        # List items in the main feed
        # Usually li.pvs-list__paged-list-item
        items = soup.find_all("li", class_="pvs-list__paged-list-item")
        
        for item in items:
            exp = Experience()
            try:
                texts = [self._clean_text(t.text) for t in item.find_all("span", class_="visually-hidden")]
                texts = [t for t in texts if t]
                
                if len(texts) >= 1: exp.title = texts[0]
                if len(texts) >= 2: exp.companyName = texts[1]
                if len(texts) >= 3: exp.startDate = texts[2] # Often date range
                if len(texts) >= 4: exp.location = texts[3]
                
                if exp.title:
                    profile.experiences.append(exp)
            except Exception as e:
                pass

    def get_education(self, profile_url, profile):
        url = f"{profile_url.rstrip('/')}/details/education/"
        print(f"Getting Education: {url}")
        self.driver.get(url)
        self._human_delay(3, 5)
        self._simulate_human_scroll()
        
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        items = soup.find_all("li", class_="pvs-list__paged-list-item")
        
        for item in items:
            edu = Education()
            try:
                texts = [self._clean_text(t.text) for t in item.find_all("span", class_="visually-hidden")]
                texts = [t for t in texts if t]
                
                if len(texts) >= 1: edu.schoolName = texts[0]
                if len(texts) >= 2: edu.degreeName = texts[1]
                if len(texts) >= 3: edu.startDate = texts[2]
                
                if edu.schoolName:
                    profile.educations.append(edu)
            except: pass

    def get_skills(self, profile_url, profile):
        url = f"{profile_url.rstrip('/')}/details/skills/"
        print(f"Getting Skills: {url}")
        self.driver.get(url)
        self._human_delay(3, 5)
        self._simulate_human_scroll()
        
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        items = soup.find_all("li", class_="pvs-list__paged-list-item")
        
        for item in items:
            skill = Skill()
            try:
                texts = [self._clean_text(t.text) for t in item.find_all("span", class_="visually-hidden")]
                if texts:
                    skill.name = texts[0]
                    # Try to find endorsements count if available
                    for t in texts:
                        if "endorsements" in t:
                            # Extract number
                            digits = "".join(filter(str.isdigit, t))
                            if digits: skill.endorsements = int(digits)
                    
                    profile.skills.append(skill)
            except: pass

    def get_posts(self, profile_url, profile):
        # Navigation
        base_url = profile_url.rstrip('/')
        url_all = f"{base_url}/recent-activity/all/"
        print(f"Getting Posts from: {url_all}")
        
        self.driver.get(url_all)
        self._human_delay(5, 7)
        
        # Initial scroll to trigger loading
        self._simulate_human_scroll()

        # Deep Scroll Loop to load more content
        # Increased limit for deeper history
        max_attempts = 25 
        min_posts_desired = 30
        
        print(" scrolling to load more posts...")
        for i in range(max_attempts):
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._human_delay(2, 4) 
            
            # Check for "Show more results" button and click it
            try:
                # Common classes for the "Show more" button in activity feed
                buttons = self.driver.find_elements(By.CLASS_NAME, "scaffold-finite-scroll__load-button")
                for btn in buttons:
                    if btn.is_displayed():
                        print("  > Clicking 'Show more results' button...")
                        self.driver.execute_script("arguments[0].click();", btn)
                        self._human_delay(3, 5) # Wait for load
            except Exception:
                pass

            # Quick check count
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            containers = soup.find_all("div", class_="feed-shared-update-v2") or \
                         soup.find_all("li", class_="profile-creator-shared-feed-update__container")
            
            count = len(containers)
            print(f"  > Scroll {i+1}/{max_attempts}: Loaded {count} posts.")
            
            if count >= min_posts_desired:
                print("  > Reached desired post count.")
                break
        
        # Final Extraction from full page source
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        
        # Selectors
        post_containers = soup.find_all("div", class_="feed-shared-update-v2") or \
                          soup.find_all("li", class_="profile-creator-shared-feed-update__container") or \
                          soup.find_all("div", class_="occludable-update")

        if not post_containers:
            print("WARNING: No post containers found with standard selectors.")
            post_containers = soup.select('div[data-urn]')

        print(f"Extracting details from {len(post_containers)} matched containers...")

        for container in post_containers:
            try:
                post = Post()
                
                # Text Content
                text_div = container.find("div", class_="feed-shared-update-v2__description-wrapper") or \
                           container.find("div", class_="feed-shared-inline-show-more-text") or \
                           container.find("div", class_="feed-shared-text") or \
                           container.find("span", class_="break-words")
                
                if text_div:
                    raw_text = text_div.get_text(separator=" ").strip()
                    post.text = self._clean_text(raw_text.replace("...see more", ""))
                
                # Author
                post.author.username = profile.linkedinUrl.split("/in/")[-1].replace("/", "")
                post.author.first_name = profile.fullName.split(" ")[0] if profile.fullName else "Unknown"
                
                # Date
                time_span = container.find("span", class_="feed-shared-actor__subtext") or \
                            container.find("a", class_="app-aware-link feed-shared-actor__subtext-link")
                
                if time_span:
                    full_time_text = self._clean_text(time_span.text)
                    post.posted_at.date = full_time_text.split("•")[0].strip()
                    post.posted_at.relative = full_time_text

                # Link
                links = container.find_all("a", href=True)
                for link in links:
                    href = link['href']
                    if "linkedin.com/feed/update" in href or "urn:li:activity" in href:
                        post.url = href.split("?")[0]
                        break
                
                # Social Stats
                social_counts = container.find("ul", class_="social-details-social-counts") or \
                                container.find("div", class_="social-details-social-activity")
                
                if social_counts:
                    # Likes
                    likes_li = social_counts.find("span", class_="social-details-social-counts__reactions-count") or \
                               social_counts.find("button", {"aria-label": lambda x: x and "reaction" in x.lower()}) or \
                               social_counts.find("span", {"aria-hidden": "true"})
                    
                    if likes_li:
                        likes_text = likes_li.text.strip()
                        digits = "".join(filter(str.isdigit, likes_text))
                        if digits: post.stats.like = int(digits)

                    # Comments
                    comments_li = social_counts.find("button", {"aria-label": lambda x: x and "comment" in x.lower()}) or \
                                  social_counts.find("li", class_="social-details-social-counts__comments")
                    if comments_li:
                         comments_text = comments_li.text.strip()
                         digits = "".join(filter(str.isdigit, comments_text))
                         if digits: post.stats.comments = int(digits)

                # Images & Media - IMPROVED
                post.media = Media(type="unknown")
                found_media = []

                # 1. Images (Standard & Delayed)
                img_tags = container.find_all("img", class_="ivm-view-attr__img--centered") or \
                           container.find_all("img", class_="update-components-image__image") or \
                           container.find_all("img", {"data-delayed-url": True}) or \
                           container.find_all("img", class_="feed-shared-article__image")
                
                for img in img_tags:
                    src = img.get("src") or img.get("data-delayed-url")
                    if src and "media.licdn.com" in src:
                        if src not in [x['url'] for x in found_media]:
                            found_media.append({"url": src, "type": "image"})

                # 2. Videos (Native Video Player)
                # LinkedIn videos are often in <video> tags or <div class="native-video-player">
                video_tags = container.find_all("video")
                for vid in video_tags:
                    # Try source tag first
                    src = vid.get("src")
                    if not src:
                        source_tag = vid.find("source")
                        if source_tag: src = source_tag.get("src")
                    
                    # If we found a video URL
                    if src:
                        found_media.append({"url": src, "type": "video"})
                    else:
                        # Fallback: grab the poster/thumbnail image
                        poster = vid.get("poster") or vid.get("data-poster-url")
                        if poster:
                            found_media.append({"url": poster, "type": "video_thumbnail"})
                
                # Assign type based on what we found first/most relevant
                if any(m['type'] == 'video' for m in found_media):
                    post.media.type = "video"
                elif any(m['type'] == 'video_thumbnail' for m in found_media):
                     post.media.type = "video" # It's a video post, but we only got the thumbnail
                elif found_media:
                    post.media.type = "image"
                
                post.media.images = found_media

                # Only filter out empty posts if truly empty
                if post.text or post.media.images:
                    profile.posts.append(post)

            except Exception as e:
                print(f"Error parsing post container: {e}")

    # --------------------------------------------------------------------------
    # Main Orchestrator
    # --------------------------------------------------------------------------

    def scrape_full_profile(self, url: str) -> Profile:
        if "linkedin.com" not in self.driver.current_url:
             self.login_and_save_cookies()
        
        # 1. Main Info + Contact Modal
        profile = self.get_profile_main(url)
        
        # 2. Details Pages
        self.get_experience(url, profile)
        self.get_education(url, profile)
        self.get_skills(url, profile)
        
        # 2b. New Details Pages
        self.get_generic_section(url, "certifications", Certification, profile.certifications)
        self.get_generic_section(url, "projects", Project, profile.projects)
        self.get_generic_section(url, "languages", Language, profile.languages)
        
        # 3. Posts
        self.get_posts(url, profile)
        
        return profile

    def close(self):
        self.driver.quit()

    def save_data(self, profile: Profile):
        filename = "pro_profile_data.json"
        data = asdict(profile)
        
        # Load existing
        try:
            with open(filename, "r", encoding="utf-8") as f:
                existing = json.load(f)
                if not isinstance(existing, list): existing = []
        except: existing = []

        # Find and Update
        updated = False
        for i, p in enumerate(existing):
            if p.get("linkedinUrl") == profile.linkedinUrl:
                existing[i] = data
                updated = True
                break
        if not updated: existing.append(data)
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        print(f"Success! Saved to {filename}")

def main():
    # --------------------------------------------------------------------------
    # LIST OF TARGET USERS
    # --------------------------------------------------------------------------
    target_urls = [
         "https://www.linkedin.com/in/satyanadella",
         # Add more URLs here, e.g.:
         # "https://www.linkedin.com/in/sundarpichai",
    ]
    
    print(f"Queue: {len(target_urls)} profiles to scrape.")
    
    scraper = LinkedInProScraper()
    try:
        # First ensure login
        scraper.login_and_save_cookies()
        
        for i, url in enumerate(target_urls):
            print(f"\n[{i+1}/{len(target_urls)}] Processing: {url}")
            
            try:
                profile = scraper.scrape_full_profile(url)
                scraper.save_data(profile)
                
                # Safety delay between profiles (VERY IMPORTANT)
                # Simulates reading, taking a break, then searching for the next person
                if i < len(target_urls) - 1:
                    wait_time = random.uniform(15, 30)
                    print(f"Waiting {int(wait_time)}s before next profile...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                print(f"Failed to scrape {url}: {e}")
                continue
            
    except Exception as e:
        print(f"Critical Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
