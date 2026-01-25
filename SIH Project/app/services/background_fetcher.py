import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.leetcode_service import fetch_leetcode_user

MAX_WORKERS = 10

INPUT_FILE = r"app/data/user_details.xlsx"
OUTPUT_FILE = r"app/data/leetcodes_data.xlsx"

def background_job():
    users_df = pd.read_excel(INPUT_FILE, engine="openpyxl")

    users_df.columns = [str(c).strip().lower() for c in users_df.columns]

    if "enabled" in users_df.columns:
        users_df = users_df[users_df["enabled"] == 1]

    usernames = [
        str(u).strip().lower()
        for u in users_df["username"]
        if str(u).strip().lower() != "nan"
    ]

    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(fetch_leetcode_user, username)
            for username in usernames
        ]

        for future in as_completed(futures):
            data = future.result()
            if data:
                results.append(data)

    pd.DataFrame(results).to_excel(
        OUTPUT_FILE,
        index=False,
        engine="openpyxl"
    )
    