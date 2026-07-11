import numpy as np
import pandas as pd
from pathlib import Path

from src.features.utils import TEAM_NAME_MAPPING, NON_FIFA_ENTITIES, normalize_team_name

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
EXTERNAL_DIR  = Path(__file__).resolve().parents[2] / "data" / "external"
FORM_WINDOW = 10
TOURNAMENT_TIERS: dict[str, int] = {
    "FIFA World Cup": 1, "UEFA Euro": 1, "Copa América": 1,
    "African Cup of Nations": 1, "AFC Asian Cup": 1, "Gold Cup": 1,
    "FIFA World Cup qualification": 2, "UEFA Euro qualification": 2,
    "African Cup of Nations qualification": 2, "AFC Asian Cup qualification": 2,
    "UEFA Nations League": 2, "CONCACAF Nations League": 2,
    "Friendly": 3,
}

def clean_team_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["home_team"] = df["home_team"].apply(normalize_team_name)
    df["away_team"] = df["away_team"].apply(normalize_team_name)

    before = len(df)
    df = df[~df["home_team"].isin(NON_FIFA_ENTITIES)]
    df = df[~df["away_team"].isin(NON_FIFA_ENTITIES)]
    # print(f"    Filtrage non-FIFA : {before - len(df)} lignes supprimées")
    return df

def add_tournament_tier(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["tournament_tier"] = df["tournament"].map(TOURNAMENT_TIERS).fillna(3).astype(int)
    return df

def compute_team_form(df: pd.DataFrame, n: int = FORM_WINDOW) -> pd.DataFrame:
    """
    Calculate form stats on N last matches from each team
    Features: home/away x form_scored / form_conceded / form_win_rate
    """
    df = df.sort_values("date").reset_index(drop=True)
    home = df[["date", "home_team", "home_score", "away_score"]].rename(
        columns={"home_team": "team", "home_score": "scored", "away_score": "conceded"})
    away = df[["date", "away_team", "away_score", "home_score"]].rename(
        columns={"away_team": "team", "away_score": "scored", "home_score": "conceded"})
    long = pd.concat([home, away], ignore_index=True)
    long["win"] = (long["scored"] > long["conceded"]).astype(int)
    long = long.sort_values(["team", "date"]).reset_index(drop=True)

    grp = long.groupby("team")
    long["form_scored"]   = grp["scored"].transform(
        lambda x: x.shift(1).ewm(span=n, min_periods=1).mean()
    )
    long["form_conceded"] = grp["conceded"].transform(
        lambda x: x.shift(1).ewm(span=n, min_periods=1).mean()
    )
    long["form_win_rate"] = grp["win"].transform(
        lambda x: x.shift(1).ewm(span=n, min_periods=1).mean()
    )

    form = long.drop_duplicates(subset=["team", "date"], keep="last")[
        ["team", "date", "form_scored", "form_conceded", "form_win_rate"]]

    df = df.merge(form, left_on=["home_team", "date"], right_on=["team", "date"], how="left")
    df.rename(columns={
        "form_scored": "home_form_scored",
        "form_conceded": "home_form_conceded",
        "form_win_rate": "home_form_win_rate",
    }, inplace=True)
    df.drop(columns=["team"], inplace=True)

    df = df.merge(form, left_on=["away_team", "date"], right_on=["team", "date"], how="left")
    df.rename(columns={
        "form_scored": "away_form_scored",
        "form_conceded": "away_form_conceded",
        "form_win_rate": "away_form_win_rate",
    }, inplace=True)
    df.drop(columns=["team"], inplace=True)

    return df

def compute_h2h(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make h2h stats on all matches

    Features:
    - h2h_matches : number of h2h
    - h2h_avg_total_goals : mean goals by h2h
    - h2h_home_win_rate : rate of win as home team
    """
    df = df.sort_values("date").reset_index(drop=True)
    df["_a"] = df[["home_team", "away_team"]].min(axis=1)
    df["_b"] = df[["home_team", "away_team"]].max(axis=1)
    df["_home_is_a"] = df["home_team"] == df["_a"]
    df["_total_goals"] = df["home_score"] + df["away_score"]
    df["_a_win"] = np.where(df["_home_is_a"],
        (df["home_score"] > df["away_score"]).astype(int),
        (df["away_score"] > df["home_score"]).astype(int))
    df["_draw"] = (df["home_score"] == df["away_score"]).astype(int)

    grp = df.groupby(["_a", "_b"])
    df["h2h_matches"] = grp.cumcount()
    df["_cum_a_wins"] = grp["_a_win"].transform(lambda x: x.shift(1).cumsum().fillna(0))
    df["_cum_draws"] = grp["_draw"].transform(lambda x: x.shift(1).cumsum().fillna(0))
    df["_cum_total_goals"] = grp["_total_goals"].transform(lambda x: x.shift(1).cumsum().fillna(0))

    df["h2h_avg_total_goals"] = np.where(df["h2h_matches"] > 0,
        df["_cum_total_goals"] / df["h2h_matches"], np.nan)
    _a_win_rate = np.where(df["h2h_matches"] > 0, df["_cum_a_wins"] / df["h2h_matches"], np.nan)
    _draw_rate = np.where(df["h2h_matches"] > 0, df["_cum_draws"] / df["h2h_matches"], np.nan)
    df["h2h_home_win_rate"] = np.where(df["_home_is_a"], _a_win_rate, 1 - _a_win_rate - _draw_rate)

    df.drop(columns=[c for c in df.columns if c.startswith("_")], inplace=True)
    return df

def load_elo_by_name() -> pd.DataFrame:
    elo = pd.read_csv(EXTERNAL_DIR / "elo_ratings.csv", parse_dates=["date"])
    codes = pd.read_csv(EXTERNAL_DIR / "elo_team_codes.csv")

    elo = elo.merge(codes, left_on="team", right_on="code", how="left")
    elo = elo.dropna(subset=["name"])
    elo = elo.rename(columns={"name": "team_name"})[["date", "team_name", "elo"]]
    elo["team_name"] = elo["team_name"].apply(normalize_team_name)
    elo = elo.sort_values("date").reset_index(drop=True)
    return elo

def add_elo_features(df: pd.DataFrame, elo: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("date").reset_index(drop=True)

    home_elo = elo.rename(columns={"team_name": "home_team", "elo": "home_elo"})
    df = pd.merge_asof(df, home_elo, on="date", by="home_team", direction="backward")

    away_elo = elo.rename(columns={"team_name": "away_team", "elo": "away_elo"})
    df = pd.merge_asof(df, away_elo, on="date", by="away_team", direction="backward")

    df["elo_diff"] = df["home_elo"] - df["away_elo"]
    return df

def build_features(input_path: Path | str | None = None, output_path: Path | str | None = None) -> pd.DataFrame:
    input_path = Path(input_path) if input_path else PROCESSED_DIR / "matches_clean.csv"
    output_path = Path(output_path) if output_path else PROCESSED_DIR / "features.csv"

    print("[1/7] Chargement")
    df = pd.read_csv(input_path, parse_dates=["date"])
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)

    print("[2/7] Normalisation & filtrage non FIFA")
    df = clean_team_names(df)

    print("[3/7] Tournament tier")
    df = add_tournament_tier(df)

    print("[4/7] Forme récente")
    df = compute_team_form(df)

    print("[5/7] Head-to-head")
    df = compute_h2h(df)

    print("[6/7] Elo rating")
    elo = load_elo_by_name()
    df = add_elo_features(df, elo)
    n_missing_elo = df["home_elo"].isna().sum() + df["away_elo"].isna().sum()
    print(f"    Valeurs Elo manquantes : {n_missing_elo}")

    print("[7/7] Targets & Sauvegarde...")
    df["total_goals"] = df["home_score"] + df["away_score"]
    df["result"] = np.where(df["home_score"] > df["away_score"], 2,
                    np.where(df["home_score"] == df["away_score"], 1, 0))

    df.to_csv(output_path, index=False)
    print(f"Done -> {output_path}  ({df.shape[0]} lignes, {df.shape[1]} colonnes)")
    return df

if __name__ == "__main__":
    build_features()