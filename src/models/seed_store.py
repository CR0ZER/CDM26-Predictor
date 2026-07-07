"""
Usage :
    python -m src.models.seed_store
"""

import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

from src.data.online.football_data_org import get_upcoming_matches
from src.features.build_features import (
    clean_team_names, add_tournament_tier, compute_team_form,
    compute_h2h, load_elo_by_name, add_elo_features,
)
from src.features.utils import resolve_model_orientation
from src.models.train_xgb import FEATURE_COLS
from src.models.evaluate import poisson_grid_probs, outcome_probs_from_grid

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "models" / "artifacts"
REPORTS_DIR   = Path(__file__).resolve().parents[2] / "models" / "reports"
STORE_PATH    = REPORTS_DIR / "predictions_store.json"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_store() -> dict:
    if not STORE_PATH.exists():
        return {}
    with open(STORE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_store(store: dict) -> None:
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def predict_single(home_team, away_team, date, neutral, base_df, elo_df, model_home, model_away):
    target_date = pd.to_datetime(date)
    df = base_df[base_df["date"] < target_date].copy()
    df["is_virtual"] = False

    feat_home, feat_away, swapped = resolve_model_orientation(home_team, away_team)

    virtual = pd.DataFrame([{
        "date":       target_date,
        "home_team":  feat_home,
        "away_team":  feat_away,
        "home_score": np.nan,
        "away_score": np.nan,
        "tournament": "FIFA World Cup",
        "city":       None,
        "country":    None,
        "neutral":    neutral,
        "is_virtual": True,
    }])

    df = pd.concat([df, virtual], ignore_index=True)
    df = clean_team_names(df)
    df = add_tournament_tier(df)
    df = compute_team_form(df)
    df = compute_h2h(df)
    df = add_elo_features(df, elo_df)
    df = df.sort_values("date").reset_index(drop=True)

    row = df[df["is_virtual"]].iloc[-1]
    X   = row[FEATURE_COLS].to_frame().T.astype(float)
    lam = float(model_home.predict(X)[0])
    mu  = float(model_away.predict(X)[0])

    if swapped:
        lam, mu = mu, lam

    grid = poisson_grid_probs(lam, mu)
    best = np.unravel_index(np.argmax(grid), grid.shape)
    p_home, p_draw, p_away = outcome_probs_from_grid(grid)

    return {
        "predicted_home": int(best[0]),
        "predicted_away": int(best[1]),
        "lambda_home":    round(lam, 3),
        "lambda_away":    round(mu, 3),
        "p_home_win":     round(p_home, 4),
        "p_draw":         round(p_draw, 4),
        "p_away_win":     round(p_away, 4),
    }


def run_seed():
    print("[1/3] Chargement des données et modèles...")
    model_home = joblib.load(ARTIFACTS_DIR / "xgb_home.pkl")
    model_away = joblib.load(ARTIFACTS_DIR / "xgb_away.pkl")
    base_df    = pd.read_csv(PROCESSED_DIR / "matches_clean.csv", parse_dates=["date"])
    base_df["home_score"] = base_df["home_score"].astype(float)
    base_df["away_score"] = base_df["away_score"].astype(float)
    elo_df = load_elo_by_name()
    store  = load_store()

    print("[2/3] Récupération des matchs terminés...")
    finished = [m for m in get_upcoming_matches(status="FINISHED") if m["home_score"] is not None]
    print(f"      {len(finished)} matchs terminés trouvés")

    print("[3/3] Seed du store...")
    n_added   = 0
    n_skipped = 0

    for i, match in enumerate(finished):
        key = f"{match['date']}|{match['home_team']}|{match['away_team']}"

        if key in store:
            n_skipped += 1
            continue

        print(f"      [{i+1}/{len(finished)}] {match['home_team']} vs {match['away_team']} ({match['date']})")

        try:
            pred = predict_single(
                match["home_team"], match["away_team"],
                match["date"], match["neutral"],
                base_df, elo_df, model_home, model_away,
            )
            store[key] = {
                "date":           match["date"],
                "home_team":      match["home_team"],
                "away_team":      match["away_team"],
                "predicted_home": pred["predicted_home"],
                "predicted_away": pred["predicted_away"],
                "lambda_home":    pred["lambda_home"],
                "lambda_away":    pred["lambda_away"],
                "p_home_win":     pred["p_home_win"],
                "p_draw":         pred["p_draw"],
                "p_away_win":     pred["p_away_win"],
                "predicted_at":   None,
                "actual_home":    int(match["home_score"]),
                "actual_away":    int(match["away_score"]),
                "result_fetched": True,
            }
            n_added += 1
        except Exception as e:
            print(f"      [WARN] {e}")

    save_store(store)
    print(f"\nDone — {n_added} matchs ajoutés, {n_skipped} déjà présents")
    print(f"Store → {STORE_PATH}")


if __name__ == "__main__":
    run_seed()