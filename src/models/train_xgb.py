import pandas as pd
import joblib
from pathlib import Path
from xgboost import XGBRegressor

from src.models.evaluate import poisson_grid_probs, outcome_probs_from_grid, evaluate_predictions

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "models" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = [
    "tournament_tier", "neutral",
    "home_form_scored", "home_form_conceded", "home_form_win_rate",
    "away_form_scored", "away_form_conceded", "away_form_win_rate",
    "h2h_matches", "h2h_avg_total_goals", "h2h_home_win_rate",
    "home_elo", "away_elo", "elo_diff",
]

XGB_PARAMS = dict(
    objective="count:poisson",
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
)


def load_data() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "features.csv", parse_dates=["date"])


def train_and_eval(df: pd.DataFrame, train_cutoff: str, test_mask) -> dict:
    train = df[df["date"] < train_cutoff]
    test = df[test_mask]

    X_train = train[FEATURE_COLS]
    X_test = test[FEATURE_COLS]

    model_home = XGBRegressor(**XGB_PARAMS).fit(X_train, train["home_score"])
    model_away = XGBRegressor(**XGB_PARAMS).fit(X_train, train["away_score"])

    lam_pred = model_home.predict(X_test)
    mu_pred = model_away.predict(X_test)

    probs_list, outcomes = [], []
    for lam, mu, (_, row) in zip(lam_pred, mu_pred, test.iterrows()):
        grid = poisson_grid_probs(float(lam), float(mu))
        probs_list.append(outcome_probs_from_grid(grid))
        outcome = 2 if row["home_score"] > row["away_score"] else (0 if row["home_score"] < row["away_score"] else 1)
        outcomes.append(outcome)

    metrics = evaluate_predictions(probs_list, outcomes)
    return metrics, model_home, model_away


if __name__ == "__main__":
    df = load_data()

    print("=== Expérience WC2022 ===")
    test_mask_2022 = (df["tournament"] == "FIFA World Cup") & \
                      (df["date"] >= "2022-11-20") & (df["date"] <= "2022-12-18")
    metrics_2022, _, _ = train_and_eval(df, "2022-11-20", test_mask_2022)
    print(f"log-loss = {metrics_2022['log_loss']:.4f} | RPS = {metrics_2022['rps_mean']:.4f}")

    print("\n=== Expérience WC2026 (matchs déjà joués) ===")
    test_mask_2026 = (df["tournament"] == "FIFA World Cup") & (df["date"] >= "2026-06-11")
    metrics_2026, model_home, model_away = train_and_eval(df, "2026-06-11", test_mask_2026)
    print(f"log-loss = {metrics_2026['log_loss']:.4f} | RPS = {metrics_2026['rps_mean']:.4f}")

    joblib.dump(model_home, ARTIFACTS_DIR / "xgb_home.pkl")
    joblib.dump(model_away, ARTIFACTS_DIR / "xgb_away.pkl")


    importances_home = pd.Series(model_home.feature_importances_, index=FEATURE_COLS).sort_values(ascending=False)
    importances_away = pd.Series(model_away.feature_importances_, index=FEATURE_COLS).sort_values(ascending=False)

    print("=== Importance — buts domicile ===")
    print(importances_home)
    print("\n=== Importance — buts extérieur ===")
    print(importances_away)