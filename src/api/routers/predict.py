import json
import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException
from pathlib import Path

from src.api.schemas import PredictionRequest, PredictionResponse, ScoreProbability
from src.models.predict import build_match_features
from src.models.train_xgb import FEATURE_COLS
from src.models.evaluate import poisson_grid_probs, outcome_probs_from_grid
from src.features.utils import resolve_model_orientation

router = APIRouter()

ARTIFACTS_DIR = Path(__file__).resolve().parents[3] / "models" / "artifacts"
STORE_PATH    = Path(__file__).resolve().parents[3] / "models" / "reports" / "predictions_store.json"

_model_home = joblib.load(ARTIFACTS_DIR / "xgb_home.pkl")
_model_away = joblib.load(ARTIFACTS_DIR / "xgb_away.pkl")


def _load_store() -> dict:
    if not STORE_PATH.exists():
        return {}
    with open(STORE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_store(store: dict) -> None:
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def _store_key(home_team: str, away_team: str, date: str) -> str:
    return f"{date}|{home_team}|{away_team}"


@router.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    date = request.date or pd.Timestamp.today().strftime("%Y-%m-%d")

    feat_home, feat_away, swapped = resolve_model_orientation(
        request.home_team, request.away_team
    )

    try:
        row = build_match_features(
            feat_home, feat_away, date, request.tournament, request.neutral
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur features : {e}")

    X   = row[FEATURE_COLS].to_frame().T.astype(float)
    lam = float(_model_home.predict(X)[0])
    mu  = float(_model_away.predict(X)[0])

    if swapped:
        lam, mu = mu, lam

    grid = poisson_grid_probs(lam, mu)
    p_home, p_draw, p_away = outcome_probs_from_grid(grid)
    n = grid.shape[0]

    p_over_2_5 = sum(grid[i, j] for i in range(n) for j in range(n) if i + j >= 3)
    p_under_2_5 = 1 - p_over_2_5
    p_btts = sum(grid[i, j] for i in range(1, n) for j in range(1, n))

    flat   = [(i, j, grid[i, j]) for i in range(n) for j in range(n)]
    top10  = sorted(flat, key=lambda t: t[2], reverse=True)[:10]
    scores = [ScoreProbability(home_goals=i, away_goals=j, probability=p) for i, j, p in top10]

    # Persistence — on écrase si le match existait déjà (prédiction plus récente = plus à jour)
    store = _load_store()
    key   = _store_key(request.home_team, request.away_team, date)
    store[key] = {
        "date":           date,
        "home_team":      request.home_team,
        "away_team":      request.away_team,
        "predicted_home": top10[0][0],
        "predicted_away": top10[0][1],
        "lambda_home":    round(lam, 3),
        "lambda_away":    round(mu, 3),
        "p_home_win":     round(p_home, 4),
        "p_draw":         round(p_draw, 4),
        "p_away_win":     round(p_away, 4),
        "predicted_at":   pd.Timestamp.now().isoformat(),
        "actual_home":    None,
        "actual_away":    None,
        "result_fetched": False,
    }
    _save_store(store)

    return PredictionResponse(
        home_team=request.home_team,
        away_team=request.away_team,
        lambda_home=lam,
        lambda_away=mu,
        p_home_win=p_home,
        p_draw=p_draw,
        p_away_win=p_away,
        most_likely_home_goals=top10[0][0],
        most_likely_away_goals=top10[0][1],
        top_scores=scores,
        score_grid=grid[:6, :6].tolist(),
        p_over_2_5=p_over_2_5,
        p_under_2_5=p_under_2_5,
        p_btts=p_btts,
    )