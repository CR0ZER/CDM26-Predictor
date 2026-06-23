import pandas as pd
from pathlib import Path

from src.models.dixon_coles import DixonColesModel
from src.models.evaluate import evaluate_predictions

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "models" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def load_data() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "matches_clean.csv", parse_dates=["date"])

def run_experiment_wc2022(df: pd.DataFrame):
    train = df[df["date"] < "2022-11-20"]
    test = df[(df["tournament"] == "FIFA World Cup") &
              (df["date"] >= "2022-11-20") & (df["date"] <= "2022-12-18")]

    print(f"[WC2022] Train : {len(train)} matchs | Test : {len(test)} matchs")

    model = DixonColesModel()
    model.fit(train)
    print(f"[WC2022] Convergé : {model.converged_} | NLL : {model.nll_:.2f} | itérations : {model.n_iter_}")
    print(f"[DEBUG] message scipy : {model.message_}")

    probs_list, outcomes = [], []
    for _, row in test.iterrows():
        probs = model.predict_outcome_probs(row["home_team"], row["away_team"])
        probs_list.append(probs)
        outcome = 2 if row["home_score"] > row["away_score"] else (0 if row["home_score"] < row["away_score"] else 1)
        outcomes.append(outcome)

    metrics = evaluate_predictions(probs_list, outcomes)
    print(f"[WC2022] log-loss = {metrics['log_loss']:.4f} | RPS = {metrics['rps_mean']:.4f}")
    return metrics, model

def run_experiment_wc2026(df: pd.DataFrame):
    train = df[df["date"] < "2026-06-11"]
    test = df[(df["tournament"] == "FIFA World Cup") & (df["date"] >= "2026-06-11")]

    print(f"\n[WC2026] Train : {len(train)} matchs | Test : {len(test)} matchs")

    model = DixonColesModel()
    model.fit(train)
    print(f"[WC2026] Convergé : {model.converged_} | NLL : {model.nll_:.2f} | itérations : {model.n_iter_}")

    probs_list, outcomes = [], []
    for _, row in test.iterrows():
        probs = model.predict_outcome_probs(row["home_team"], row["away_team"])
        probs_list.append(probs)
        outcome = 2 if row["home_score"] > row["away_score"] else (0 if row["home_score"] < row["away_score"] else 1)
        outcomes.append(outcome)

    metrics = evaluate_predictions(probs_list, outcomes)
    print(f"[WC2026] log-loss = {metrics['log_loss']:.4f} | RPS = {metrics['rps_mean']:.4f}")
    return metrics, model

if __name__ == "__main__":
    df = load_data()
    metrics_2022, model_2022 = run_experiment_wc2022(df)
    metrics_2026, model_2026 = run_experiment_wc2026(df)
    model_2026.save(ARTIFACTS_DIR / "dixon_coles_baseline.pkl")