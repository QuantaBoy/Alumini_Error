import requests
from datetime import datetime

# GraphQL query for user profile stats
QUERY = """
query userPublicProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      ranking
      reputation
      realName
      countryName
      starRating
      aboutMe
      userAvatar
    }
    submitStats: submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
        submissions
      }
    }
  }
}
"""

def fetch_leetcode_user(username):
    """
    Fetches public LeetCode user profile data using GraphQL.
    """
    url = "https://leetcode.com/graphql"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://leetcode.com/",
        "Origin": "https://leetcode.com",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": QUERY,
        "variables": {"username": username}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {"error": f"LeetCode API Error: {response.status_code}"}
            
        data = response.json()
        
        if "errors" in data:
            return {"error": data["errors"][0]["message"]}
            
        user_data = data.get("data", {}).get("matchedUser")
        
        if not user_data:
            return {"error": "User not found"}
            
        profile = user_data.get("profile", {})
        stats = user_data.get("submitStats", {}).get("acSubmissionNum", [])
        
        # Parse stats
        solved_count = {s["difficulty"]: s["count"] for s in stats}
        total_solved = sum(s["count"] for s in stats if s["difficulty"] != "All")
        
        # If 'All' is present, use it directly for total
        for s in stats:
            if s["difficulty"] == "All":
                total_solved = s["count"]
                break

        return {
            "username": user_data.get("username", username),
            "real_name": profile.get("realName"),
            "avatar": profile.get("userAvatar"),
            "ranking": profile.get("ranking", "N/A"),
            "reputation": profile.get("reputation", 0),
            "country": profile.get("countryName"),
            "total_solved": total_solved,
            "easy_solved": solved_count.get("Easy", 0),
            "medium_solved": solved_count.get("Medium", 0),
            "hard_solved": solved_count.get("Hard", 0),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except requests.exceptions.Timeout:
        return {"error": "LeetCode request timed out"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
