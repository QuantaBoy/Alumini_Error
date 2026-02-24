import requests
import os
from collections import defaultdict
from datetime import datetime
import math

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = "https://api.github.com"

if not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_TOKEN not found in environment")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def _get(url, params=None, retries=1):
    try:
        # INCREASED TIMEOUT to 30s to prevent ReadTimeout errors for larger profiles
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        if r.status_code != 200:
            with open("debug_sync.txt", "a") as f:
                f.write(f"API Error [{r.status_code}]: {url}\n")
            raise RuntimeError(f"GitHub API failed: {url} | {r.status_code}")
            
        return r.json(), r.headers
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        if retries > 0:
            print(f"GitHub request timed out. Retrying... ({url})")
            import time
            time.sleep(2)
            return _get(url, params, retries - 1)
        raise e
    except Exception as e:
        with open("debug_sync.txt", "a") as f:
            f.write(f"Network/Code Error: {str(e)}\n")
        raise e

def fetch_github_profile(username):
    data, _ = _get(f"{BASE_URL}/users/{username}")

    created = datetime.fromisoformat(data["created_at"].replace("Z", ""))
    account_age_days = (datetime.utcnow() - created).days

    return {
        "username": data["login"],
        "name": data["name"],
        "bio": data["bio"],
        "followers": data["followers"],
        "following": data["following"],
        "public_repos": data["public_repos"],
        "account_age_days": account_age_days,
        "profile_url": data["html_url"]
    }

def fetch_all_repos(username):
    repos = []
    page = 1

    while True:
        data, _ = _get(
            f"{BASE_URL}/users/{username}/repos",
            params={"per_page": 100, "page": page}
        )
        if not data:
            break
        repos.extend(data)
        page += 1

    return repos

def fetch_repo_languages(owner, repo_name):
    data, _ = _get(f"{BASE_URL}/repos/{owner}/{repo_name}/languages")
    return list(data.keys())

def analyse_repo(owner, repo):
    created = datetime.fromisoformat(repo["created_at"].replace("Z", ""))
    pushed = datetime.fromisoformat(repo["pushed_at"].replace("Z", ""))

    active_days = (pushed - created).days
    last_push_days_ago = (datetime.utcnow() - pushed).days

    if last_push_days_ago > 180:
        status = "Dead"
    elif last_push_days_ago <= 30:
        status = "Active"
    elif active_days > 120:
        status = "Serious Project"
    else:
        status = "Maintained"

    languages = fetch_repo_languages(owner, repo["name"])

    return {
        "name": repo["name"],
        "description": repo["description"],
        "stars": repo["stargazers_count"],
        "forks": repo["forks_count"],
        "issues": repo["open_issues_count"],
        "active_days": active_days,
        "last_push_days_ago": last_push_days_ago,
        "status": status,
        "languages": languages,
        "repo_url": repo["html_url"]
    }

def build_language_intelligence(repo_analyses):
    lang_stats = defaultdict(lambda: {
        "repos": 0,
        "active_repos": 0,
        "total_active_days": 0,
        "stars": 0
    })

    for repo in repo_analyses:
        is_active = repo["last_push_days_ago"] <= 90
        for lang in repo["languages"]:
            s = lang_stats[lang]
            s["repos"] += 1
            s["total_active_days"] += repo["active_days"]
            s["stars"] += repo["stars"]
            if is_active:
                s["active_repos"] += 1

    result = {}

    for lang, s in lang_stats.items():
        avg_active_days = s["total_active_days"] / s["repos"]

        proficiency = (
            0.4 * min(s["repos"] / 5, 1) +
            0.4 * min(avg_active_days / 180, 1) +
            0.2 * min(s["active_repos"] / 3, 1)
        )

        result[lang] = {
            "repos": s["repos"],
            "active_repos": s["active_repos"],
            "avg_active_days": round(avg_active_days, 1),
            "stars": s["stars"],
            "proficiency": round(proficiency, 3),
            "level": (
                "Mastered" if proficiency >= 0.75 else
                "Proficient" if proficiency >= 0.5 else
                "Familiar"
            )
        }

    return result

def build_activity_summary(repo_analyses):
    total = len(repo_analyses)
    active = sum(1 for r in repo_analyses if r["status"] != "Dead")
    dead = total - active

    avg_life = (
        sum(r["active_days"] for r in repo_analyses) / total
        if total else 0
    )

    last_activity = min(
        (r["last_push_days_ago"] for r in repo_analyses),
        default=None
    )

    return {
        "total_repos": total,
        "active_repos": active,
        "dead_repos": dead,
        "avg_repo_lifespan_days": round(avg_life, 2),
        "last_activity_days_ago": last_activity
    }

def compute_developer_score(repo_analyses, language_intelligence):
    total_repos = len(repo_analyses)

    if total_repos == 0:
        return {
            "consistency": 0,
            "depth": 0,
            "impact": 0,
            "overall": 0
        }

    recent_repos = sum(
        1 for r in repo_analyses
        if r["last_push_days_ago"] <= 90
    )

    consistency = recent_repos / total_repos

    top_langs = sorted(
        language_intelligence.values(),
        key=lambda x: x["proficiency"],
        reverse=True
    )[:3]

    depth = (
        sum(l["proficiency"] for l in top_langs) / len(top_langs)
        if top_langs else 0
    )

    impact_raw = sum(
        r["stars"] + r["forks"] for r in repo_analyses
    )

    impact = min(math.log(impact_raw + 1, 10) / 3, 1.0)

    overall = min(
        1.0,
        0.4 * consistency +
        0.4 * depth +
        0.2 * impact
    )

    return {
        "consistency": round(consistency, 3),
        "depth": round(depth, 3),
        "impact": round(impact, 3),
        "overall": round(overall, 3)
    }

def build_full_github_profile(username):
    profile = fetch_github_profile(username)
    repos = fetch_all_repos(username)

    repo_analyses = []

    for repo in repos:
        if repo["fork"]:
            continue
        analysis = analyse_repo(username, repo)
        if analysis["status"] == "Dead" and analysis["stars"] == 0:
            continue
        repo_analyses.append(analysis)

    language_intelligence = build_language_intelligence(repo_analyses)
    activity = build_activity_summary(repo_analyses)
    score = compute_developer_score(repo_analyses, language_intelligence)

    return {
        "github_profile": profile,
        "activity_summary": activity,
        "language_intelligence": language_intelligence,
        "repo_quality": repo_analyses,
        "developer_score": score,
        "last_synced_at": datetime.utcnow().isoformat()
    }
