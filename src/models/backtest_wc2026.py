"""
Usage :
    python -m src.models.backtest_wc2026
"""

import json
from datetime import datetime
from pathlib import Path

from src.data.online.football_data_org import get_upcoming_matches

REPORTS_DIR  = Path(__file__).resolve().parents[2] / "models" / "reports"
STORE_PATH   = REPORTS_DIR / "predictions_store.json"
BACKTEST_PATH = REPORTS_DIR / "wc2026_backtest.json"


def run_backtest():
    print("[1/3] Chargement du store de prédictions...")
    if not STORE_PATH.exists():
        print("      Aucun store trouvé — lance d'abord des prédictions via l'interface.")
        return

    with open(STORE_PATH, encoding="utf-8") as f:
        store = json.load(f)

    print(f"      {len(store)} prédictions stockées")

    print("[2/3] Récupération des vrais résultats...")
    finished = get_upcoming_matches(status="FINISHED")
    results_map = {
        f"{m['date']}|{m['home_team']}|{m['away_team']}": m
        for m in finished
        if m["home_score"] is not None
    }

    print("[3/3] Comparaison et calcul des métriques...")
    results = []
    n_skipped = 0

    for key, pred in store.items():
        real = results_map.get(key)
        if real is None:
            n_skipped += 1
            continue  # match pas encore joué ou clé non trouvée

        actual_home = int(real["home_score"])
        actual_away = int(real["away_score"])

        actual_outcome = 2 if actual_home > actual_away else (0 if actual_home < actual_away else 1)
        pred_outcome   = 2 if pred["predicted_home"] > pred["predicted_away"] else (0 if pred["predicted_home"] < pred["predicted_away"] else 1)

        results.append({
            "date":                pred["date"],
            "home_team":           pred["home_team"],
            "away_team":           pred["away_team"],
            "actual_home":         actual_home,
            "actual_away":         actual_away,
            "predicted_home":      pred["predicted_home"],
            "predicted_away":      pred["predicted_away"],
            "lambda_home":         pred["lambda_home"],
            "lambda_away":         pred["lambda_away"],
            "p_home_win":          pred["p_home_win"],
            "p_draw":              pred["p_draw"],
            "p_away_win":          pred["p_away_win"],
            "predicted_at":        pred.get("predicted_at"),
            "outcome_correct":     actual_outcome == pred_outcome,
            "exact_score_correct": actual_home == pred["predicted_home"] and actual_away == pred["predicted_away"],
        })

    results.sort(key=lambda r: r["date"])

    n = len(results)
    if n == 0:
        print("      Aucun match prédit trouvé parmi les matchs terminés.")
        return

    n_outcome_ok = sum(1 for r in results if r["outcome_correct"])
    n_exact_ok   = sum(1 for r in results if r["exact_score_correct"])

    output = {
        "generated_at":        datetime.now().isoformat(),
        "n_matches":           n,
        "n_skipped":           n_skipped,
        "outcome_correct":     n_outcome_ok,
        "outcome_accuracy":    round(n_outcome_ok / n, 4),
        "exact_score_correct": n_exact_ok,
        "exact_score_accuracy": round(n_exact_ok / n, 4),
        "matches":             results,
    }

    with open(BACKTEST_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nRésultats :")
    print(f"  Prédictions évaluées : {n} ({n_skipped} ignorées — match pas encore joué)")
    print(f"  Résultat correct     : {n_outcome_ok}/{n} ({output['outcome_accuracy']*100:.1f}%)")
    print(f"  Score exact          : {n_exact_ok}/{n} ({output['exact_score_accuracy']*100:.1f}%)")
    print(f"\nSauvegardé → {BACKTEST_PATH}")


if __name__ == "__main__":
    run_backtest()