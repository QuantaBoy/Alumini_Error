import requests
import re
try:
    import cloudscraper
except ImportError:
    cloudscraper = None

def fetch_codeforces_user(username):
    """
    Fetches Codeforces user data including basic info, submissions, and rating history.
    """
    if not username:
        return None

    # sanitize input: remove spaces, extract handle if full URL is pasted
    username = username.strip()
    if "/" in username:
        username = username.split("/")[-1]

    # Use a browser-like User-Agent to avoid 403 Forbidden errors
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # -------- USER INFO --------
        info_url = f"https://codeforces.com/api/user.info?handles={username}"
        try:
            if cloudscraper:
                scraper = cloudscraper.create_scraper()
                info_resp = scraper.get(info_url, timeout=10)
            else:
                info_resp = requests.get(info_url, headers=headers, timeout=10)
        except requests.exceptions.RequestException as e:
            return {"error": f"Network error connecting to Codeforces: {str(e)}"}

        if info_resp.status_code == 404:
             return {"error": f"User '{username}' not found on Codeforces."}
        elif info_resp.status_code == 403:
             return {"error": "Codeforces blocked the request (403). Try again later."}
        elif info_resp.status_code == 429:
             return {"error": "Too many requests to Codeforces. Please wait."}
        elif info_resp.status_code != 200:
             return {"error": f"Codeforces API error: Status {info_resp.status_code}"}

        try:
            info_data = info_resp.json()
        except ValueError:
            return {"error": f"Invalid response from Codeforces (Status {info_resp.status_code})"}
        
        if info_data.get("status") != "OK":
            return {"error": f"API Error: {info_data.get('comment', 'Unknown error')}"}
            
        user_info = info_data["result"][0]

        # -------- SUBMISSIONS --------
        recent_submissions = []
        try:
            status_url = f"https://codeforces.com/api/user.status?handle={username}"
            if cloudscraper:
                status_resp = scraper.get(status_url, timeout=10)
            else:
                status_resp = requests.get(status_url, headers=headers, timeout=10)
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                if status_data.get("status") == "OK":
                    for sub in status_data["result"][:5]:
                        problem_name = sub.get("problem", {}).get("name", "Unknown Problem")
                        verdict = sub.get("verdict", "Unknown Verdict")
                        recent_submissions.append({"problem": problem_name, "verdict": verdict})
        except Exception:
            pass # Fail silently for sub-data

        # -------- RATING HISTORY --------
        rating_history = []
        try:
            rating_url = f"https://codeforces.com/api/user.rating?handle={username}"
            if cloudscraper:
                rating_resp = scraper.get(rating_url, timeout=10)
            else:
                rating_resp = requests.get(rating_url, headers=headers, timeout=10)
            if rating_resp.status_code == 200:
                rating_data = rating_resp.json()
                if rating_data.get("status") == "OK":
                    for contest in rating_data["result"][:5]:
                        rating_history.append({
                            "contest": contest.get("contestName"),
                            "newRating": contest.get("newRating"),
                            "rank": contest.get("rank")
                        })
        except Exception:
            pass # Fail silently for sub-data
        
        return {
            "username": user_info.get("handle"),
            "rating": user_info.get("rating"),
            "rank": user_info.get("rank"),
            "max_rating": user_info.get("maxRating"),
            "max_rank": user_info.get("maxRank"),
            "recent_submissions": recent_submissions,
            "rating_history_sample": rating_history,
            "full_info": user_info
        }

    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
