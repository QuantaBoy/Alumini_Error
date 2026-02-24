import time
import json
import random
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
import os
import pickle
import re
from datetime import datetime

# Ensure undetected_chromedriver and selenium are available.
# If they're missing, do NOT exit the whole process during import —
# raise a clear runtime error when the scraper is instantiated instead.
_HAS_DEPS = True
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError as e:
    _HAS_DEPS = False
    print("CRITICAL ERROR: specific libraries are missing.")
    print(f"Details: {e}")
    print("Please run: pip install -r requirements.txt (undetected-chromedriver selenium beautifulsoup4)")

    class LinkedInProScraper:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "LinkedIn scraper dependencies are not installed. Install requirements and restart the app."
            )
    # Provide minimal placeholders to avoid NameErrors elsewhere if referenced accidentally
    By = None
    WebDriverWait = None
    EC = None

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
        
        # Stability Flags for Undetected Chromedriver
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--ignore-certificate-errors")
        
        # Local user data directory to avoid path/permission issues on Windows
        import uuid
        user_data_dir = os.path.abspath(os.path.join(os.getcwd(), ".uc_profile"))
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir, exist_ok=True)
        options.add_argument(f"--user-data-dir={user_data_dir}")

        # NOTE: LinkedIn heavily restricts headless browsers on feed/activity pages.
        # We run in a visible window by default. Set LINKEDIN_HEADFUL=1 to keep it visible intentionally.
        # Headless mode is intentionally disabled to avoid being blocked by LinkedIn.
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-dev-shm-usage")
        # NOTE: Do NOT disable images - LinkedIn's feed needs images enabled to render JS properly

        if use_proxy and proxy_string:
            print(f"Configuring Proxy: {proxy_string}")
            options.add_argument(f'--proxy-server={proxy_string}')

        max_startup_retries = 2
        for i in range(max_startup_retries):
            try:
                # Cleanup zombie processes on Windows
                if os.name == 'nt' and i == 0:
                    try: os.system("taskkill /f /im chromedriver.exe /t >nul 2>&1")
                    except: pass

                self._log_debug(f"Starting uc.Chrome (Attempt {i+1})...")
                driver = uc.Chrome(options=options, version_main=None)
                
                # Critical: wait for browser to fully initialize
                time.sleep(5)
                
                # Quick check if it's responsive
                _ = driver.current_url
                self._log_debug("Chrome initialized successfully.")
                return driver
            except Exception as e:
                self._log_debug(f"Chrome initialization attempt {i+1} failed: {e}")
                if i == max_startup_retries - 1:
                    raise e
                time.sleep(3)

    def _is_driver_alive(self):
        """Check if the driver is still responsive."""
        try:
            if not self.driver: return False
            # Simple check that doesn't trigger a navigation
            _ = self.driver.current_url
            return True
        except Exception:
            return False

    # --------------------------------------------------------------------------
    # Human Simulation
    # --------------------------------------------------------------------------

    def _human_delay(self, min_seconds=2, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def _simulate_human_scroll(self, max_scrolls=15):
        """Standard human-like scrolling down the page with a safety limit."""
        try:
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            current_position = self.driver.execute_script("return window.pageYOffset")
            scrolls = 0
            
            while current_position < total_height and scrolls < max_scrolls:
                scroll_step = random.randint(400, 800) 
                current_position += scroll_step
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(0.8, 1.5))
                
                # Occasional pause/scroll up
                if random.random() < 0.1:
                    current_position -= random.randint(100, 200)
                    self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                    time.sleep(random.uniform(1.0, 2.0))
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height > total_height:
                    total_height = new_height
                
                scrolls += 1
                if current_position >= total_height:
                    break
            
            self._log_debug(f"Finished scrolling. Scrolls done: {scrolls}")
        except Exception as e:
            self._log_debug(f"Scroll failed gently: {e}")

    def _log_debug(self, msg: str):
        """Internal helper to log to debug_sync.txt"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("debug_sync.txt", "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [Scraper] {msg}\n")
        except:
            pass

    def _clean_text(self, text: Optional[str]) -> str:
        if not text: return ""
        return " ".join(text.split()).strip()

    # --------------------------------------------------------------------------
    # Session
    # --------------------------------------------------------------------------

    def login_and_save_cookies(self):
        print("Checking session state...")
        
        # Initial navigation with retry
        max_nav_retries = 2
        for attempt in range(max_nav_retries):
            try:
                if not self._is_driver_alive():
                    print(f"Driver not alive before navigation (attempt {attempt+1})")
                    return # Scraper will catch this in scrape_full_profile
                
                self.driver.get("https://www.linkedin.com/login")
                time.sleep(4)
                break
            except Exception as e:
                print(f"Login page load attempt {attempt+1} failed: {e}")
                if attempt == max_nav_retries - 1:
                    return
                time.sleep(3)

        # Cookie loading with basic integrity check
        # Use absolute path based on script location to avoid CWD-dependent issues
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        _project_root = os.path.dirname(os.path.dirname(_script_dir))  # app/services -> app -> project root
        cookie_file = os.path.join(_project_root, "linkedin_cookies.pkl")
        print(f"Looking for cookies at: {cookie_file}")
        if os.path.exists(cookie_file) and os.path.getsize(cookie_file) > 64:
            print("Loading cookies...")
            try:
                with open(cookie_file, "rb") as f:
                    cookies = pickle.load(f)
                
                # Filter cookies to avoid domain mismatch errors
                for cookie in cookies:
                    try:
                        # uc sometimes gets grumpy if we don't fix expiry types
                        if 'expiry' in cookie:
                            cookie['expiry'] = int(cookie['expiry'])
                        self.driver.add_cookie(cookie)
                    except Exception:
                        pass
                
                self.driver.get("https://www.linkedin.com/feed/")
                time.sleep(5)
            except Exception as e:
                print(f"Error applying cookies: {e}")
        
        if "feed" in self.driver.current_url:
            print("Logged in successfully via cookies!")
            return

        # Chrome is running in visible (non-headless) mode.
        # If cookies failed, show the action-required prompt and wait for manual login.
        print(f"Session expired or cookies invalid. Current URL: {self.driver.current_url}")
        if "checkpoint" in self.driver.current_url:
            print("LinkedIn security checkpoint detected! Please resolve it in the browser window.")
        
        print("\n" + "="*50)
        print("ACTION REQUIRED: Log in manually to the LinkedIn window that just opened.")
        print("The app will wait up to 2 minutes for you to log in.")
        print("="*50 + "\n")
        
        # Wait up to 2 minutes for manual login
        start_time = time.time()
        while "feed" not in self.driver.current_url and (time.time() - start_time) < 120:
            time.sleep(2)
        
        if "feed" in self.driver.current_url:
            print("Login detected! Saving cookies for future use...")
            try:
                pickle.dump(self.driver.get_cookies(), open(cookie_file, "wb"))
                print(f"Cookies saved to: {cookie_file}")
            except Exception as e:
                print(f"Failed to save cookies: {e}")
        else:
            print("Login timed out or failed.")

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
        self._log_debug(f"Navigating to Profile: {url}")
        try:
            self.driver.get(url)
            self._human_delay(3, 5) 
        except Exception as e:
            self._log_debug(f"Failed to navigate to profile: {e}")
            return Profile(linkedinUrl=url)

        if not self._is_driver_alive():
            return Profile(linkedinUrl=url)
        
        # Check for Common Roadblocks
        current_url = self.driver.current_url.lower()
        if "login" in current_url or "checkpoint" in current_url or "security" in current_url:
            self._log_debug(f"Scraper blocked: {self.driver.current_url}")
        
        self._log_debug("Starting initial page scroll...")
        self._simulate_human_scroll(max_scrolls=5) # profile top doesn't need much

        if not self._is_driver_alive():
            return Profile(linkedinUrl=url)

        # Attempt to expand collapsed sections
        self._log_debug("Attempting to expand sections...")
        try:
            expand_selectors = [
                "//button[contains(normalize-space(.),'See more')]",
                "//button[contains(normalize-space(.),'see more')]",
                "//button[contains(@aria-label,'See more')]",
                ".inline-show-more-text__button",
                ".pv-profile-section__card-action-bar button",
            ]
            for sel in expand_selectors:
                try:
                    if sel.startswith("//"):
                        els = self.driver.find_elements(By.XPATH, sel)
                    else:
                        els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    for el in els:
                        try:
                            if el and el.is_displayed():
                                el.click()
                                time.sleep(0.5)
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

        # Wait for name tag to ensure page is settled
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        except:
            print("Timed out waiting for H1 name tag. Proceeding anyway...")

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        profile = Profile(linkedinUrl=url)

        # DEBUG: Save a snippet of the page source if things look empty
        if not soup.find("h1"):
            print(f"WARNING: Name tag (H1) not found. Page might not have rendered or is a restricted view. URL: {self.driver.current_url}")
        
        # Basic Info
        try:
            # 1. Full Name - Multiple common selectors
            name_tag = (
                soup.find("h1", class_="text-heading-xlarge") or
                soup.find("h1", class_="top-card-layout__title") or
                soup.select_one(".pv-top-card-layout__title") or
                soup.select_one("h1.v-align-middle") or
                soup.find("h1")
            )
            profile.fullName = self._clean_text(name_tag.text) if name_tag else ""
            if not profile.fullName:
                # Try to get from title tag as fallback
                title_tag = soup.find("title")
                if title_tag and "|" in title_tag.text:
                    profile.fullName = self._clean_text(title_tag.text.split("|")[0])
            
            print(f"Extracted Name: {profile.fullName}")

            # 2. Headline
            headline_tag = (
                soup.find("div", class_="text-body-medium") or
                soup.find("p", class_="top-card-layout__headline") or
                soup.find("div", class_="text-body-medium break-words")
            )
            profile.headline = self._clean_text(headline_tag.text) if headline_tag else ""

            # 3. Location
            loc_tag = (
                soup.find("span", class_="text-body-small inline t-black--light break-words") or
                soup.find("span", class_="top-card-layout__first-subline") or
                soup.find("div", class_="pb2 pv-text-details__left-panel")
            )
            profile.location = self._clean_text(loc_tag.text) if loc_tag else ""
            
            # 4. About - Robust Extraction
            about_section = soup.find("section", {"id": "about"}) or soup.select_one("section.about-section")
            
            if not about_section:
                for h in soup.find_all(['h2', 'h3', 'h4', 'h5']):
                    if h.get_text().lower().strip() == "about":
                        parent = h.find_parent("section") or h.find_parent("div", class_="pv-profile-card")
                        if parent:
                            about_section = parent
                            break

            if about_section:
                print("Found About section, extracting text...")
                 
                # 1. Look for specialized containers first
                containers = [
                    about_section.find("div", class_="pv-shared-text-with-see-more"),
                    about_section.find("div", class_="inline-show-more-text"),
                    about_section.find("div", class_="display-flex ph5 pv3"),
                    about_section.select_one(".pv-profile-card__about-contents")
                ]
                 
                bio_text = ""
                for c in containers:
                    if not c: continue
                     
                    # Look for hidden full text span inside container
                    hidden = c.find("span", class_="visually-hidden")
                    txt = self._clean_text(hidden.get_text() if hidden else c.get_text())
                     
                    # Check if this text is actually a bio
                    if txt and txt.lower() != "about" and len(txt) > 10:
                        bio_text = txt
                        break

                # 2. General span search within section if still empty
                if not bio_text:
                    spans = about_section.find_all("span")
                    for s in spans:
                        txt = self._clean_text(s.get_text())
                        if len(txt) > 20 and txt.lower() != "about" and "see more" not in txt.lower():
                            bio_text = txt
                            break

                # 3. Final cleaning
                if bio_text:
                    # Remove "About" prefix or "see more"
                    bio_text = re.sub(r'^about\s+', '', bio_text, flags=re.IGNORECASE).strip()
                    bio_text = bio_text.replace("...see more", "").replace("see more", "").strip()
                    
                    # Double check it isn't just "About" now
                    if bio_text.lower() == "about":
                        bio_text = ""
                
                profile.about = bio_text
                print(f"Extracted About (len): {len(profile.about)}")
            else:
                print("ABORT: About section element not found in soup.")
                # Save a debug snapshot of the current page to help diagnose selector issues
                try:
                    fname = f"linkedin_about_debug_{int(time.time())}.html"
                    with open(fname, "w", encoding="utf-8") as fh:
                        fh.write(self.driver.page_source)
                    print(f"Saved debug HTML snippet to {fname}")
                except Exception as dex:
                    print("Failed to save debug HTML snippet:", dex)
            
            # 5. Profile Pic (High Quality from img tag)
            img_tag = (
                soup.find("img", class_="pv-top-card-profile-picture__image") or
                soup.find("img", class_="top-card-layout__entity-image") or
                soup.select_one("img.pv-top-card-profile-picture__image") or
                soup.select_one(".pv-top-card-profile-picture__image img")
            )
            if img_tag:
                profile.profilePic = img_tag.get("src") or img_tag.get("data-delayed-url") or ""
                print(f"Found Profile Pic URL: {profile.profilePic[:50]}...")
            else:
                print("ABORT: Profile picture image tag not found.")
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
        self._human_delay(8, 12)  # Wait longer for activity feed to initialize
        print(f"  > Activity feed URL after navigation: {self.driver.current_url}")
        
        # Deep Scroll Loop
        max_attempts = 3 # Increased scrolls
        min_posts_desired = 10
        
        # Selectors for identifying post containers
        post_selectors_css = 'div.feed-shared-update-v2, li.profile-creator-shared-feed-update__container, div.occludable-update, div[data-urn^="urn:li:activity:"], .scaffold-finite-scroll__content > div'

        print(f" scrolling up to {max_attempts} times to load posts...")
        for i in range(max_attempts):
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._human_delay(3, 5) 
            
            # Check for "Show more results" button and click it
            try:
                # Common classes for the "Show more" button in activity feed
                btn_selectors = [
                    ".scaffold-finite-scroll__load-button",
                    "button.artdeco-button--muted",
                    "//button[contains(., 'Show more')]",
                    "//button[contains(., 'Load more')]"
                ]
                for sel in btn_selectors:
                    try:
                        if sel.startswith("//"):
                            btns = self.driver.find_elements(By.XPATH, sel)
                        else:
                            btns = self.driver.find_elements(By.CSS_SELECTOR, sel)
                        
                        for btn in btns:
                            if btn.is_displayed():
                                print("  > Clicking 'Show more results' button...")
                                self.driver.execute_script("arguments[0].click();", btn)
                                self._human_delay(4, 6)
                                break
                    except: pass
            except Exception:
                pass

            # Quick check count
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            containers = soup.select(post_selectors_css)
            
            count = len(containers)
            print(f"  > Scroll {i+1}/{max_attempts}: Loaded {count} posts.")
            
            if count >= min_posts_desired:
                print("  > Reached desired post count.")
                break
        
        # Final Extraction
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        post_containers = soup.select(post_selectors_css)

        if not post_containers:
            print(f"WARNING: No post containers found. Page structure might have changed. URL: {self.driver.current_url}")
            # Try last-ditch effort to find any urn
            post_containers = soup.select('div[data-urn]')

        print(f"Extracting details from {len(post_containers)} matched containers...")

        for container in post_containers:
            try:
                # Basic check to avoid non-post elements if using broad selectors
                if not container.get('data-urn') and 'update' not in str(container.get('class')):
                     if not container.find('span', class_='break-words'):
                         continue

                post = Post()
                
                # Text Content - Use broader search
                text_selectors = [
                    "div.feed-shared-update-v2__description-wrapper",
                    "div.feed-shared-inline-show-more-text",
                    "div.feed-shared-text",
                    "div.update-components-text",
                    "span.break-words",
                    ".update-components-text span"
                ]
                
                text_div = None
                for sel in text_selectors:
                    if sel.startswith('.'):
                        text_div = container.select_one(sel)
                    else:
                        # Try both find and select_one for complex class names
                        text_div = container.select_one(sel.replace('div.', 'div').replace('span.', 'span'))
                    if text_div: break
                
                if text_div:
                    raw_text = text_div.get_text(separator=" ").strip()
                    post.text = self._clean_text(raw_text.replace("...see more", ""))
                
                # Author Info
                try:
                    username_part = profile.linkedinUrl.split("/in/")[-1].replace("/", "")
                    post.author.username = username_part
                    post.author.first_name = profile.fullName.split(" ")[0] if profile.fullName else "Unknown"
                except: pass
                
                # Date/Time
                time_tag = container.select_one("span.feed-shared-actor__subtext, a.feed-shared-actor__subtext-link, .update-components-actor__subtext span")
                if time_tag:
                    full_time_text = self._clean_text(time_tag.text)
                    post.posted_at.date = full_time_text.split("•")[0].strip()
                    post.posted_at.relative = full_time_text

                # Link to post
                links = container.find_all("a", href=True)
                for link in links:
                    href = link['href']
                    if "linkedin.com/feed/update" in href or "urn:li:activity" in href:
                        post.url = href.split("?")[0]
                        if not post.url.startswith("http"):
                             post.url = f"https://www.linkedin.com{post.url}"
                        break
                
                # Social Stats
                social_counts = container.select_one(".social-details-social-counts, .social-details-social-activity, .update-v2-social-counts")
                if social_counts:
                    # Likes/Reactions
                    likes_count = social_counts.select_one(".social-details-social-counts__reactions-count, button[aria-label*='reaction'], span[aria-hidden='true']")
                    if likes_count:
                        digits = "".join(filter(str.isdigit, likes_count.text))
                        if digits: post.stats.like = int(digits)

                    # Comments
                    comments_count = social_counts.select_one("button[aria-label*='comment'], .social-details-social-counts__comments")
                    if comments_count:
                         digits = "".join(filter(str.isdigit, comments_count.text))
                         if digits: post.stats.comments = int(digits)

                    # Reposts
                    reposts_count = social_counts.select_one("button[aria-label*='repost'], .social-details-social-counts__reposts")
                    if reposts_count:
                         digits = "".join(filter(str.isdigit, reposts_count.text))
                         if digits: post.stats.reposts = int(digits)

                # Media Extraction
                post.media = Media(type="unknown")
                found_media = []

                # Images
                img_tags = container.select("img.ivm-view-attr__img--centered, img.update-components-image__image, img[data-delayed-url], img.feed-shared-article__image")
                for img in img_tags:
                    src = img.get("src") or img.get("data-delayed-url")
                    if src and "media.licdn.com" in src:
                        if src not in [x['url'] for x in found_media]:
                            found_media.append({"url": src, "type": "image"})

                # Videos
                video_tags = container.find_all("video")
                for vid in video_tags:
                    src = vid.get("src") or (vid.find("source").get("src") if vid.find("source") else None)
                    if src:
                        found_media.append({"url": src, "type": "video"})
                    else:
                        poster = vid.get("poster") or vid.get("data-poster-url")
                        if poster:
                            found_media.append({"url": poster, "type": "video_thumbnail"})
                
                if any(m['type'] == 'video' for m in found_media):
                    post.media.type = "video"
                elif found_media:
                    post.media.type = "image"
                post.media.images = found_media

                if post.text or post.media.images:
                    profile.posts.append(post)

            except Exception as e:
                print(f"Error parsing post container: {e}")

    # --------------------------------------------------------------------------
    # Main Orchestrator
    # --------------------------------------------------------------------------

    def scrape_full_profile(self, url_or_username: str) -> Profile:
        # Construct full URL if just a username or partial URL is provided
        url = url_or_username.strip().strip('/')
        
        if not url.startswith("http"):
            if "linkedin.com/in/" in url:
                url = f"https://{url}"
            else:
                url = f"https://www.linkedin.com/in/{url}/"
        
        self._log_debug(f"Starting full scrape for: {url}")

        # Ensure empty profile setup
        profile = Profile(linkedinUrl=url)

        # Always attempt login
        self.login_and_save_cookies()
        
        if not self._is_driver_alive():
            self._log_debug("Driver died after login attempt.")
            return profile

        # 1. Main Info + Contact Modal
        self._log_debug("Fetching main profile info...")
        profile = self.get_profile_main(url)
        if not self._is_driver_alive(): return profile
        
        # 2. Details Pages
        self._log_debug("Fetching experience...")
        self.get_experience(url, profile)
        if not self._is_driver_alive(): return profile
        
        self._log_debug("Fetching education...")
        self.get_education(url, profile)
        if not self._is_driver_alive(): return profile
        
        self._log_debug("Fetching skills...")
        self.get_skills(url, profile)
        if not self._is_driver_alive(): return profile
        
        # 2b. New Details Pages
        self._log_debug("Fetching certifications, projects, languages...")
        self.get_generic_section(url, "certifications", Certification, profile.certifications)
        self.get_generic_section(url, "projects", Project, profile.projects)
        self.get_generic_section(url, "languages", Language, profile.languages)
        
        if not self._is_driver_alive(): return profile

        # 3. Posts
        self._log_debug("Fetching posts...")
        self.get_posts(url, profile)
        
        self._log_debug(f"Scrape completed for {profile.fullName}")
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
    # MANUAL TESTING
    # --------------------------------------------------------------------------
    target_input = input("Enter LinkedIn URL or Username to scrape (comma separated): ")
    if not target_input.strip():
        print("No input provided. Exiting.")
        return

    target_urls = [t.strip() for t in target_input.split(",") if t.strip()]
    
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