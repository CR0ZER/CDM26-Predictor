import json
from fastapi import APIRouter, HTTPException
from pathlib import Path

from src.data.online.football_data_org import get_upcoming_matches

router = APIRouter()

REPORTS_DIR = Path(__file__).resolve().parents[3] / "models" / "reports"
STORE_PATH  = REPORTS_DIR / "predictions_store.json"


def load_store() -> dict:
    if not STORE_PATH.exists():
        return {}
    with open(STORE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_store(store: dict) -> None:
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def compute_stats(store: dict) -> dict:
    from datetime import datetime

    evaluated = [v for v in store.values() if v.get("result_fetched") and v.get("actual_home") is not None]
    n = len(evaluated)

    results = []
    for v in sorted(evaluated, key=lambda x: x["date"], reverse=True):
        actual_home = v["actual_home"]
        actual_away = v["actual_away"]
        pred_home   = v["predicted_home"]
        pred_away   = v["predicted_away"]

        actual_outcome = 2 if actual_home > actual_away else (0 if actual_home < actual_away else 1)
        pred_outcome   = 2 if pred_home > pred_away else (0 if pred_home < pred_away else 1)

        results.append({
            "date":                v["date"],
            "home_team":           v["home_team"],
            "away_team":           v["away_team"],
            "actual_home":         actual_home,
            "actual_away":         actual_away,
            "predicted_home":      pred_home,
            "predicted_away":      pred_away,
            "lambda_home":         v["lambda_home"],
            "lambda_away":         v["lambda_away"],
            "p_home_win":          v["p_home_win"],
            "p_draw":              v["p_draw"],
            "p_away_win":          v["p_away_win"],
            "outcome_correct":     actual_outcome == pred_outcome,
            "exact_score_correct": actual_home == pred_home and actual_away == pred_away,
        })

    n_outcome_ok = sum(1 for r in results if r["outcome_correct"])
    n_exact_ok   = sum(1 for r in results if r["exact_score_correct"])

    return {
        "generated_at":         datetime.now().isoformat(),
        "n_matches":            n,
        "outcome_correct":      n_outcome_ok,
        "outcome_accuracy":     round(n_outcome_ok / n, 4) if n else 0,
        "exact_score_correct":  n_exact_ok,
        "exact_score_accuracy": round(n_exact_ok / n, 4) if n else 0,
        "matches":              results,
    }


@router.get("/backtest")
def get_backtest():
    store = load_store()
    if not store:
        raise HTTPException(status_code=404, detail="Store vide — lancer seed_store.py d'abord")
    return compute_stats(store)


@router.post("/backtest/refresh")
def refresh_backtest():
    """
    Récupère les vrais scores pour tous les matchs prédits
    dont result_fetched=False, met à jour le store.
    """
    store = load_store()

    pending = {k: v for k, v in store.items() if not v.get("result_fetched")}
    if not pending:
        return {"updated": 0, "message": "Aucun match en attente de résultat"}

    finished = get_upcoming_matches(status="FINISHED")
    results_map = {
        f"{m['date']}|{m['home_team']}|{m['away_team']}": m
        for m in finished
        if m["home_score"] is not None
    }

    n_updated = 0
    for key, pred in pending.items():
        real = results_map.get(key)
        if real is None:
            continue
        store[key]["actual_home"]    = int(real["home_score"])
        store[key]["actual_away"]    = int(real["away_score"])
        store[key]["result_fetched"] = True
        n_updated += 1

    save_store(store)
    stats = compute_stats(store)

    return {
        "updated": n_updated,
        "stats":   stats,
    }