import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.features.utils import normalize_football_data_name, is_neutral_venue

load_dotenv()

BASE_URL = "https://api.football-data.org/v4"
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
HEADERS = {"X-Auth-Token": API_KEY}
COMPETITION_CODE = "WC"


def get_upcoming_matches(status: str = "SCHEDULED") -> list[dict]:
    url = f"{BASE_URL}/competitions/{COMPETITION_CODE}/matches"
    params = {"status": status} if status else {}

    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    matches = []
    for m in data.get("matches", []):
        if m["homeTeam"]["name"] is None or m["awayTeam"]["name"] is None:
            continue
        home_name = normalize_football_data_name(m["homeTeam"]["name"])
        away_name = normalize_football_data_name(m["awayTeam"]["name"])
        full_time = m.get("score", {}).get("fullTime", {})

        utc_time = datetime.fromisoformat(m["utcDate"].replace('Z', '+00:00'))
        utc_plus_2 = utc_time + timedelta(hours=2)
        matches.append({
            "id": m["id"],
            "date": utc_plus_2.strftime("%Y-%m-%d"),
            "time": utc_plus_2.strftime("%H:%M"),
            "home_team": home_name,
            "away_team": away_name,
            "stage": m.get("stage"),
            "group": m.get("group"),
            "status": m.get("status"),
            "neutral": is_neutral_venue(home_name, away_name),
            "home_score": full_time.get("home"),
            "away_score": full_time.get("away"),
        })
    return matches