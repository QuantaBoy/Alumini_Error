import requests
from datetime import datetime

COOKIES = {
    "LEETCODE_SESSION": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0MTE4OTQ5LCJ1c2VybmFtZSI6InN1cmFqYXZhIiwiZXhwIjoxNzQxMTA1NTQyfQ.1_2_6029x-5x5_q57r22048815081015101710191018",
    "csrftoken": "PASTE_VALUE_HERE"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://leetcode.com",
    "X-CSRFToken": COOKIES["csrftoken"]
}

QUERY = """
query userProfile($username: String!) {
  matchedUser(username: $username) {
    submitStats {
      acSubmissionNum {
        difficulty
        count
      }
    }
    profile {
      ranking
      reputation
    }
  }
}
"""

def fetch_leetcode_user(username):
    r = requests.post(
        "https://leetcode.com/graphql",
        json={"query": QUERY, "variables": {"username": username}},
        headers=HEADERS,
        cookies=COOKIES,
        timeout=10
    )

    data = r.json()
    user = data.get("data", {}).get("matchedUser")
    if not user:
        return None

    stats = {
        s["difficulty"]: s["count"]
        for s in user["submitStats"]["acSubmissionNum"]
    }

    easy = stats.get("Easy", 0)
    medium = stats.get("Medium", 0)
    hard = stats.get("Hard", 0)

    return {
        "username": username,
        "easy_solved": easy,
        "medium_solved": medium,
        "hard_solved": hard,
        "total_solved": easy + medium + hard,  # ✅ FIXED
        "ranking": user["profile"]["ranking"],
        "reputation": user["profile"]["reputation"],
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
