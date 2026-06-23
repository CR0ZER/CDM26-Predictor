import time
import requests
import pandas as pd
from pathlib import Path

EXTERNAL_DIR = Path(__file__).resolve().parents[3] / "data" / "external"
EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
BASE_URL  = "https://www.eloratings.net/"
HEADERS   = {"User-Agent": "Mozilla/5.0"}
DELAY_SEC = 0.5

def get_team_names() -> dict[str, str]:
    """Parsing en.teams.tsv"""
    resp = requests.get(
        url=BASE_URL + "en.teams.tsv",
        headers=HEADERS,
        timeout=15
    )
    resp.encoding = "utf-8"
    resp.raise_for_status()

    teams = {}
    for line in resp.text.strip().split("\n"):
        parts = line.strip().split("\t")
        if len(parts) < 2:
            continue
        code = parts[0].strip()
        name = parts[1].strip()
        if code and name and "_loc" not in code:
            teams[code] = name
    pd.DataFrame(list(teams.items()), columns=["code", "name"]).to_csv(
        EXTERNAL_DIR / "elo_team_codes.csv", index=False
    )
    return teams

def parse_team_csv(tsv_text: str, team_code: str) -> list[dict]:
    """
    Parse team TSV
    Col :
        0:year  1:month  2:day  3:home  4:away  5:h_score  6:a_score
        7:tournament  8:?  9:elo_change  10:home_elo  11:away_elo
        12:?  13:?  14:home_rank  15:away_rank
    """
    rows = []
    for line in tsv_text.strip().split("\n"):
        parts = line.strip().split("\t")
        if len(parts) < 12:
            continue
        try:
            year  = parts[0].strip()
            month = parts[1].strip().zfill(2)
            day   = parts[2].strip().zfill(2)

            if day == "00":
                day = "01"
            if month == "00":
                month = "01"

            home_code = parts[3].strip()
            away_code = parts[4].strip()

            def clean_float(s: str) -> float | None:
                s = s.replace("â", "").replace("+", "").strip()
                return float(s) if s and s not in ("-", "") else None

            home_elo = clean_float(parts[10])
            away_elo = clean_float(parts[11])

            if home_elo is None or away_elo is None:
                continue

            date_str = f"{year}-{month}-{day}"

            rows.append({"date": date_str, "team": home_code, "elo": home_elo})
            rows.append({"date": date_str, "team": away_code, "elo": away_elo})

        except (ValueError, IndexError):
            continue
    return rows

def scrape_elo(test_mode: bool = False) -> pd.DataFrame:
    """
    Main pipeline
    """
    print("[1/3] Récupération des équipes")
    teams = get_team_names()
    print(f"    {len(teams)} équipes trouvées")

    if test_mode:
        sample = dict(list(teams.items())[:5])
        print(f"    Mode test : {list(sample.values())}")
        teams = sample
    
    all_rows: list[dict] = []
    errors: list[str] = []
    total = len(teams)

    print(f"[2/3] Téléchargement ({total} équipes, ~{total * DELAY_SEC:.0f}s)")
    for i, (code, name) in enumerate(teams.items()):
        url = BASE_URL + name.replace(" ", "_") + ".tsv"
        try:
            resp = requests.get(url=url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                rows = parse_team_csv(resp.text, code)
                all_rows.extend(rows)
                if (i + 1) % 25 == 0 or test_mode:
                    print(f"    {i+1}/{total} - {name} ({len(rows)//2} matches)")
                elif resp.status_code == 404:
                    errors.append(name)
        except Exception as e:
            errors.append(f"{name}: {e}")
        
        time.sleep(DELAY_SEC)
    
    if errors:
        print(f"\n[WARN] {len(errors)} équipes non trouvées : {errors[:10]}")
    
    print("[3/3] Construction du DataFrame")
    df = pd.DataFrame(all_rows)
    
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    df = df.drop_duplicates(subset=["date", "team"]).sort_values(["team", "date"]).reset_index(drop=True)

    return df

if __name__ == "__main__":
    df = scrape_elo(test_mode=False)
    output_path = EXTERNAL_DIR / "elo_ratings.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSauvegardé → {output_path}")
    print(f"Shape final : {df.shape}")
    print(f"Équipes uniques : {df['team'].nunique()}")
    print(f"Période : {df['date'].min()} → {df['date'].max()}")