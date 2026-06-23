from pydantic import BaseModel, Field
from typing import Optional

class PredictionRequest(BaseModel):
    home_team: str = Field(..., examples=["France"])
    away_team: str = Field(..., examples=["Brazil"])
    date: Optional[str] = Field(default=None, description="Format YYYY-MM-DD, par défaut aujourd'hui")
    tournament: str = "FIFA World Cup"
    neutral: bool = True

class ScoreProbability(BaseModel):
    home_goals: int
    away_goals: int
    probability: float

class PredictionResponse(BaseModel):
    home_team: str
    away_team: str
    lambda_home: float
    lambda_away: float

    p_home_win: float
    p_draw: float
    p_away_win: float

    most_likely_home_goals: int
    most_likely_away_goals: int

    top_scores: list[ScoreProbability]
    score_grid: list[list[float]]

    p_over_2_5: float
    p_under_2_5: float
    p_btts: float