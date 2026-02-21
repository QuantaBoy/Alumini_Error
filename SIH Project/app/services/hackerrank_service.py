import requests
from concurrent.futures import ThreadPoolExecutor


def fetch_hackerrank_user(username):
    """
    Fetches HackerRank profile data (profile info + badges/solved counts)
    for a given username using HackerRank's public REST API.
    Returns a dict with profile data, or {"error": "..."} on failure.
    """
    base_profile_url = f"https://www.hackerrank.com/rest/contests/master/hackers/{username}/profile"
    badges_url = f"https://www.hackerrank.com/rest/hackers/{username}/badges"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }

    def get_url(url):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_profile = executor.submit(get_url, base_profile_url)
        future_badges = executor.submit(get_url, badges_url)

        profile_data = future_profile.result()
        badges_data = future_badges.result()

    if not profile_data:
        return {"error": f"User '{username}' not found or profile is private."}

    model = profile_data.get("model", {})

    # ── Basic Info ──────────────────────────────────────────────────────────
    result = {
        "username":       model.get("username", username),
        "name":           model.get("name", "N/A"),
        "country":        model.get("country", "N/A"),
        "school":         model.get("school", "N/A"),
        "rank":           model.get("personal_rank", "N/A"),
        "followers":      model.get("followers_count", 0),
        "profile_url":    f"https://www.hackerrank.com/{username}",
    }

    # ── Badges & Solved Count ────────────────────────────────────────────────
    badges_list = []
    total_solved = 0

    if badges_data and "models" in badges_data:
        for badge in badges_data["models"]:
            stars  = badge.get("stars", 0)
            solved = badge.get("solved", 0)
            if stars > 0 or solved > 0:
                badges_list.append({
                    "badge_name": badge.get("badge_name", "Unknown"),
                    "stars":      stars,
                    "solved":     solved,
                })
                total_solved += solved

    result["total_solved"] = total_solved
    result["badges"]       = badges_list

    return result
