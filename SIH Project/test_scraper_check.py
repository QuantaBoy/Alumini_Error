"""
LinkedIn Scraper Diagnostic Check
Run with: python test_scraper_check.py
"""
import os
import sys
import pickle

print("=" * 55)
print("  LinkedIn Scraper Diagnostic")
print("=" * 55)

# 1. Check dependencies
print("\n[1] Checking dependencies...")
try:
    import undetected_chromedriver as uc
    print("  [OK] undetected_chromedriver: v" + uc.__version__)
except ImportError as e:
    print("  [MISSING] undetected_chromedriver: " + str(e))
    print("  --> Fix: pip install undetected-chromedriver")

try:
    import selenium
    print("  [OK] selenium: v" + selenium.__version__)
except ImportError as e:
    print("  [MISSING] selenium: " + str(e))
    print("  --> Fix: pip install selenium")

try:
    from bs4 import BeautifulSoup
    print("  [OK] beautifulsoup4")
except ImportError as e:
    print("  [MISSING] beautifulsoup4: " + str(e))
    print("  --> Fix: pip install beautifulsoup4")

# 2. Check cookies file
print("\n[2] Checking LinkedIn cookies...")
script_dir = os.path.dirname(os.path.abspath(__file__))
cookie_file = os.path.join(script_dir, "linkedin_cookies.pkl")
if os.path.exists(cookie_file):
    size = os.path.getsize(cookie_file)
    print("  [OK] Cookie file found: " + cookie_file)
    print("     Size: " + str(size) + " bytes")
    if size > 64:
        try:
            with open(cookie_file, "rb") as f:
                cookies = pickle.load(f)
            li_cookies = [c for c in cookies if "linkedin" in c.get("domain", "")]
            print("     LinkedIn-domain cookies: " + str(len(li_cookies)))
            has_li_at = any(c.get("name") == "li_at" for c in cookies)
            if has_li_at:
                print("     Has 'li_at' session cookie: YES (session is likely valid)")
            else:
                print("     Has 'li_at' session cookie: NO (may need re-login)")
        except Exception as e:
            print("  [ERROR] Cookie file unreadable: " + str(e))
    else:
        print("  [WARN] Cookie file too small (" + str(size) + " bytes) -- likely invalid/empty")
else:
    print("  [MISSING] Cookie file NOT found at: " + cookie_file)
    print("     First run will open a browser for manual login.")

# 3. Check ChromeDriver cache
print("\n[3] Checking cached ChromeDriver...")
appdata = os.environ.get("APPDATA", "")
candidate = os.path.join(appdata, "undetected_chromedriver", "undetected_chromedriver.exe")
if os.path.exists(candidate):
    size = os.path.getsize(candidate)
    print("  [OK] Cached chromedriver found: " + candidate)
    print("     Size: " + str(size) + " bytes")
else:
    print("  [WARN] No cached chromedriver at: " + candidate)
    print("     It will be auto-downloaded on first run (requires internet).")

# 4. Check Chrome browser
print("\n[4] Checking Google Chrome installation...")
chrome_paths = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
]
chrome_found = False
for p in chrome_paths:
    if os.path.exists(p):
        print("  [OK] Chrome found at: " + p)
        chrome_found = True
        break
if not chrome_found:
    print("  [MISSING] Chrome not found. Please install Google Chrome.")

# 5. Check .uc_profile user-data-dir
print("\n[5] Checking Chrome user-data-dir (.uc_profile)...")
uc_profile = os.path.join(script_dir, ".uc_profile")
if os.path.isdir(uc_profile):
    print("  [OK] .uc_profile dir exists: " + uc_profile)
else:
    print("  [INFO] .uc_profile not yet created (will be created on first run)")

# 6. Check scraper import
print("\n[6] Checking scraper module import...")
try:
    sys.path.insert(0, script_dir)
    from app.services.linkedin_scraper import LinkedInProScraper, Profile, Post
    print("  [OK] linkedin_scraper module imports successfully")
except Exception as e:
    print("  [ERROR] Import failed: " + str(e))

# 7. Check sync service
print("\n[7] Checking linkedin_sync_service...")
try:
    from app.services.linkedin_sync_service import sync_linkedin_for_user
    print("  [OK] linkedin_sync_service imports OK")
except Exception as e:
    print("  [ERROR] Import failed: " + str(e))

# 8. Check debug_sync.txt for recent errors
print("\n[8] Checking debug_sync.txt for errors...")
debug_file = os.path.join(script_dir, "debug_sync.txt")
if os.path.exists(debug_file):
    with open(debug_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    print("  Found " + str(len(lines)) + " lines in debug_sync.txt")
    if lines:
        print("  Last 15 lines:")
        for line in lines[-15:]:
            print("    " + line.rstrip())
else:
    print("  [INFO] debug_sync.txt not found (no sync run yet)")

print("\n" + "=" * 55)
print("  Diagnostic complete.")
print("=" * 55)
