from fastapi import APIRouter, HTTPException
from pathlib import Path
import joblib
import pandas as pd

from src.api.schemas import PredictionRequest, PredictionResponse, ScoreProbability
from src.models.predict import build_match_features
from src.models.train_xgb import FEATURE_COLS
from src.models.evaluate import poisson_grid_probs, outcome_probs_from_grid
from src.features.utils import resolve_model_orientation

router = APIRouter()

ARTIFACTS_DIR = Path(__file__).resolve().parents[3] / "models" / "artifacts"
_model_home = joblib.load(ARTIFACTS_DIR / "xgb_home.pkl")
_model_away = joblib.load(ARTIFACTS_DIR / "xgb_away.pkl")

@router.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    date = request.date or pd.Timestamp.today().strftime("%Y-%m-%d")

    feat_home_team, feat_away_team, swapped = resolve_model_orientation(request.home_team, request.away_team)

    try:
        row = build_match_features(
            feat_home_team, feat_away_team,
            date, request.tournament,
            request.neutral
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur de construction des features : {e}")
    
    X = row[FEATURE_COLS].to_frame().T.astype(float)
    lam = float(_model_home.predict(X)[0])
    mu = float(_model_away.predict(X)[0])

    if swapped:
        lam, mu = mu, lam

    grid = poisson_grid_probs(lam, mu)
    p_home, p_draw, p_away = outcome_probs_from_grid(grid)
    n = grid.shape[0]

    p_over_2_5 = sum(grid[i, j] for i in range(n) for j in range(n) if i + j >= 3)
    p_under_2_5 = 1 - p_over_2_5
    p_btts = sum(grid[i, j] for i in range(1, n) for j in range(1, n))

    flat = [(i, j, grid[i, j]) for i in range(n) for j in range(n)]
    top10 = sorted(flat, key=lambda t: t[2], reverse=True)[:10]
    top_scores = [ScoreProbability(home_goals=i, away_goals=j, probability=p) for i, j, p in top10]

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
        top_scores=top_scores,
        score_grid=grid[:6, :6].tolist(),
        p_over_2_5=p_over_2_5,
        p_under_2_5=p_under_2_5,
        p_btts=p_btts,
    )