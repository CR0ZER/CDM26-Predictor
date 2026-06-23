"""
Usage :
    python -m src.models.predict --home France --away Brazil --date 2026-06-20
"""
import argparse
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

from src.features.build_features import (
    clean_team_names, add_tournament_tier, compute_team_form,
    compute_h2h, load_elo_by_name, add_elo_features,
)
from src.models.train_xgb import FEATURE_COLS
from src.models.evaluate import poisson_grid_probs, outcome_probs_from_grid
from src.features.utils import resolve_model_orientation
from src.data.online.football_data_org import get_upcoming_matches

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "models" / "artifacts"


def build_match_features(home_team, away_team, date, tournament, neutral):
    target_date = pd.to_datetime(date)

    df = pd.read_csv(PROCESSED_DIR / "matches_clean.csv", parse_dates=["date"])
    df["home_score"] = df["home_score"].astype(float)
    df["away_score"] = df["away_score"].astype(float)

    try:
        finished = get_upcoming_matches(status="FINISHED")
        existing_keys = set(
            df.loc[df["tournament"] == "FIFA World Cup", ["date", "home_team", "away_team"]]
            .apply(lambda r: (r["date"], r["home_team"], r["away_team"]), axis=1)
        )
        new_rows = []
        for m in finished:
            m_date = pd.to_datetime(m["date"])
            if m_date > target_date:
                continue
            key = (m_date, m["home_team"], m["away_team"])
            if key not in existing_keys and m["home_score"] is not None:
                new_rows.append({
                    "date": m_date,
                    "home_team": m["home_team"],
                    "away_team": m["away_team"],
                    "home_score": float(m["home_score"]),
                    "away_score": float(m["away_score"]),
                    "tournament": "FIFA World Cup",
                    "city": None,
                    "country": None,
                    "neutral": m["neutral"],
                })
        if new_rows:
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            print(f"[predict] {len(new_rows)} match(s) CdM 2026 intégrés (jusqu'au {date})")
    except Exception as e:
        print(f"[predict] Avertissement : rafraîchissement impossible ({e})")

    df["is_virtual"] = False

    virtual_row = pd.DataFrame([{
        "date": target_date,
        "home_team": home_team,
        "away_team": away_team,
        "home_score": np.nan,
        "away_score": np.nan,
        "tournament": tournament,
        "city": None,
        "country": None,
        "neutral": neutral,
        "is_virtual": True,
    }])

    df = pd.concat([df, virtual_row], ignore_index=True)
    df = clean_team_names(df)
    df = add_tournament_tier(df)
    df = compute_team_form(df)
    df = compute_h2h(df)

    elo = load_elo_by_name()
    df = add_elo_features(df, elo)

    df = df.sort_values("date").reset_index(drop=True)
    virtual = df[df["is_virtual"]]
    return virtual.iloc[-1]


def predict_match(home_team: str, away_team: str, date: str, tournament: str, neutral: bool) -> dict:
    feat_home, feat_away, swapped = resolve_model_orientation(home_team, away_team)
    row = build_match_features(feat_home, feat_away, date, tournament, neutral)
    X = row[FEATURE_COLS].to_frame().T.astype(float)

    model_home = joblib.load(ARTIFACTS_DIR / "xgb_home.pkl")
    model_away = joblib.load(ARTIFACTS_DIR / "xgb_away.pkl")

    lam = float(model_home.predict(X)[0])
    mu = float(model_away.predict(X)[0])

    if swapped:
        lam, mu = mu, lam

    grid = poisson_grid_probs(lam, mu)
    p_home, p_draw, p_away = outcome_probs_from_grid(grid)
    best_idx = np.unravel_index(np.argmax(grid), grid.shape)

    flat = [(i, j, grid[i, j]) for i in range(grid.shape[0]) for j in range(grid.shape[1])]
    top3 = sorted(flat, key=lambda t: t[2], reverse=True)[:3]

    return {
        "home_team": home_team, "away_team": away_team,
        "lambda_home": lam, "lambda_away": mu,
        "predicted_score": best_idx,
        "p_home_win": p_home, "p_draw": p_draw, "p_away_win": p_away,
        "top3_scores": top3,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", required=True, help="Équipe à domicile (ex: France)")
    parser.add_argument("--away", required=True, help="Équipe à l'extérieur (ex: Brazil)")
    parser.add_argument("--date", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    parser.add_argument("--tournament", default="FIFA World Cup")
    parser.add_argument("--non-neutral", dest="neutral", action="store_false", default=True,
                         help="À activer si une des deux équipes joue chez elle (terrain non neutre)")
    args = parser.parse_args()

    result = predict_match(args.home, args.away, args.date, args.tournament, args.neutral)

    print(f"\n{result['home_team']} vs {result['away_team']}")
    print(f"λ domicile = {result['lambda_home']:.2f} | λ extérieur = {result['lambda_away']:.2f}")
    print(f"\nProbabilités : Domicile {result['p_home_win']*100:.1f}% | Nul {result['p_draw']*100:.1f}% | Extérieur {result['p_away_win']*100:.1f}%")
    print(f"\nScore le plus probable : {result['predicted_score'][0]}-{result['predicted_score'][1]}")
    print("\nTop 3 scores exacts :")
    for i, j, p in result["top3_scores"]:
        print(f"  {i}-{j} : {p*100:.1f}%")