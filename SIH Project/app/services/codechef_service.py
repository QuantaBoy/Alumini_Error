import requests
from bs4 import BeautifulSoup
import re

def fetch_codechef_user(username):
    url = f"https://www.codechef.com/users/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return {"error": f"Failed to fetch profile (Status: {response.status_code})"}
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. Basic Info
        # 1. Basic Info
        name_tag = soup.find("h1")
        rating_div = soup.find("div", class_="rating-number")
        current_rating = "N/A"
        if rating_div:
            # The rating number is usually the first text node, followed by a <small> or <i> tag for "Provisional"
            # We can just extract the integer from the text
            raw_text = rating_div.get_text(strip=True)
            # Use regex to find the first sequence of digits
            match = re.search(r'^(\d+)', raw_text)
            if match:
                current_rating = match.group(1)
            else:
                 current_rating = raw_text # Fallback
        stars_tag = soup.find("div", class_="rating-star")
        
        # 2. Ranks
        global_rank = "N/A"
        country_rank = "N/A"
        ranks_div = soup.find("div", class_="rating-ranks")
        if ranks_div:
            # CodeChef ranks are usually in <strong> inside <li>
            rank_items = ranks_div.find_all("li")
            for item in rank_items:
                text = item.get_text(strip=True).lower()
                val = item.find("strong")
                if "global" in text and val:
                    global_rank = val.get_text(strip=True)
                elif "country" in text and val:
                    country_rank = val.get_text(strip=True)
        
        # 3. Solved Problems Count
        total_solved = "0"
        # Search for any tag containing the text
        solved_text = soup.find(string=re.compile(r"Total Problems Solved:\s*(\d+)"))
        if solved_text:
            match = re.search(r"Total Problems Solved:\s*(\d+)", solved_text)
            if match:
                total_solved = match.group(1)
        else:
            # Fallback to h3 search
            h3_solved = soup.find("h3", string=re.compile(r"Total Problems Solved"))
            if h3_solved:
                match = re.search(r"(\d+)", h3_solved.get_text())
                if match: total_solved = match.group(1)
        
        # 4. Courses Completed (Learning Paths)
        courses_count = "0"
        learning_paths_text = soup.find(string=re.compile(r"Learning Paths\s*\((\d+)\)"))
        if learning_paths_text:
            match = re.search(r"Learning Paths\s*\((\d+)\)", learning_paths_text)
            if match:
                courses_count = match.group(1)
        
        # 5. Sectional Breakdown & Difficulty Detection
        breakdown = {}
        difficulty_data = {"Easy": 0, "Medium": 0, "Hard": 0}
        found_difficulty = False
        
        solved_section = soup.find("section", class_="rating-data-section problems-solved")
        if solved_section:
            headers = solved_section.find_all(["h3", "h5"])
            for h in headers:
                h_text = h.get_text(strip=True)
                match = re.search(r"^(.*?)\s*\((\d+)\)", h_text)
                if match:
                    cat_name, count = match.groups()
                    if ":" in cat_name: cat_name = cat_name.split(":")[-1].strip()
                    
                    # Check for Difficulty
                    for diff in difficulty_data.keys():
                        if diff.lower() in cat_name.lower():
                            difficulty_data[diff] = count
                            found_difficulty = True
                    
                    breakdown[cat_name.strip()] = count
                elif ":" in h_text:
                    parts = h_text.split(":")
                    if len(parts) == 2 and parts[1].strip().isdigit():
                        breakdown[parts[0].strip()] = parts[1].strip()
        
        return {
            "Username": username,
            "Name": name_tag.get_text(strip=True) if name_tag else "N/A",
            "Star Rating": stars_tag.get_text(strip=True) if stars_tag else "N/A",
            "Current Rating": current_rating,
            "Global Rank": global_rank,
            "Country Rank": country_rank,
            "Total Problems Solved": total_solved,
            "Courses Completed": courses_count,
            "Difficulty Breakdown": difficulty_data if found_difficulty else None,
            "Section Breakdown": breakdown
        }
        
    except Exception as e:
        return {"error": str(e)}
