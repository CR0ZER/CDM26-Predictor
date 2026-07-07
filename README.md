# 🏆 CdM26 Predictor

![Python](https://img.shields.io/badge/python-3.12+-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white) ![React](https://img.shields.io/badge/React-20232A.svg?logo=react&logoColor=61DAFB) ![XGBoost](https://img.shields.io/badge/XGBoost-ML%20model-orange.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg)

> Complete machine learning pipeline to predict 2026 FIFA World Cup match scores : from data collection to an interactive web interface.

---

## Table of Contents

- [🏆 CdM26 Predictor](#-cdm26-predictor)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
  - [Features](#features)
  - [Tech Stack](#tech-stack)
  - [Model Results](#model-results)
  - [Architecture](#architecture)
  - [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [Backend](#backend)
    - [Frontend](#frontend)
  - [Running the Project](#running-the-project)
  - [API](#api)
  - [Data Sources](#data-sources)
  - [Known Limitations](#known-limitations)
  - [License](#license)
  - [Author](#author)

---

## About

Personal project developed during the 2026 World Cup itself. The goal: predict the score of upcoming matches through a complete ML pipeline (data collection → feature engineering → modeling → API → web interface), built on more than 24,000 international matches since 1993.

The project goes beyond a simple 1X2 model (win/draw/loss): it directly models each team's expected goals using a Poisson regression approach, producing a full exact-score distribution rather than just a single outcome.

## Features

- Day-by-day navigation through the 2026 World Cup schedule (upcoming and completed matches, fetched live)
- Predict a single match or an entire matchday in one click
- 1X2 probabilities, full exact-score grid (heatmap), over/under 2.5 goals, BTTS (both teams to score)
- Match cards with flags, organized by matchday in a Sofascore-style layout
- Home-advantage handling for the three co-host nations (USA, Mexico, Canada)
- Live model performance tracking — outcome accuracy and exact-score accuracy updated after each matchday

## Tech Stack

| Component | Choice |
|---|---|
| Main model | XGBoost (two Poisson regressions — home / away goals) |
| Baseline model | Dixon-Coles (bivariate Poisson regression, analytical-gradient optimization) |
| Backend | FastAPI |
| Frontend | React (Vite) + Recharts |
| Historical data | Kaggle (international results, 1872–2026) |
| Rankings | Elo ratings (eloratings.net) |
| Live schedule | football-data.org API |

## Model Results

Evaluated on the 2022 World Cup matches (64 games), used as a temporal test set — training strictly prior in time, no data leakage:

| Model | Log-loss | RPS |
|---|---|---|
| Dixon-Coles (baseline) | 1.0611 | 0.2209 |
| **XGBoost** | **0.9208** | **0.1813** |
| Improvement | **-13.2%** | **-17.9%** |

Feature importance analysis shows that the Elo ranking (differential + absolute values) accounts for roughly 70% of the model's predictive power, ahead of recent form and head-to-head history.
 
Live performance on the 2026 World Cup (updated throughout the tournament) is tracked directly in the app via the **Model Stats** panel.

## Architecture
 
```
data sources (Kaggle, Elo, football-data.org)
        │
        ▼
  feature engineering (form, h2h, Elo, competition tier)
        │
        ▼
  models (Dixon-Coles baseline + XGBoost)
        │
        ▼
   FastAPI (/api/matches, /api/predict, /api/backtest, /api/backtest/refresh)
        │
        ▼
   React (match cards, stats heatmap, live model performance panel)
        │
        ▼
   predictions_store.json (persistent prediction log)
```

## Installation

### Prerequisites
- Python 3.12+
- Node.js 20+ (LTS)
- A [Kaggle](https://www.kaggle.com) account and a [football-data.org](https://www.football-data.org/client/register) account for API keys

### Backend

```bash
git clone https://github.com/CR0ZER/CDM26-Predictor.git
cd cdm26_predictor

python -m venv cdm_venv
source cdm_venv/bin/activate      # Windows: cdm_venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env              # then fill in your API keys
```

### Frontend

```bash
cd frontend
npm install
```

## Running the Project

Processed data and trained models are already included in the repo (`data/processed/`, `models/artifacts/`) — no need to rerun the full pipeline to start the app.

**Backend:**
```bash
uvicorn src.api.main:app --reload
```
→ API at `http://127.0.0.1:8000`, interactive docs at `/docs`

**Frontend:**
```bash
cd frontend
npm run dev
```
→ App at `http://localhost:5173`

**Seed the prediction store** (first-time setup, populates past World Cup matches):
```bash
python -m src.models.seed_store
```

**To regenerate the full pipeline** (optional):
```bash
python src/data/download.py
python src/data/scraping/elo_ratings.py
python -m src.features.build_features
python -m src.models.train          # Dixon-Coles baseline
python -m src.models.train_xgb      # main model
```

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/matches` | Match schedule (upcoming and finished) |
| `POST` | `/api/predict` | Full prediction (1X2, score grid, over/under 2.5, BTTS) — auto-saved to store |
| `GET` | `/api/backtest` | Model performance stats computed from the prediction store |
| `POST` | `/api/backtest/refresh` | Fetch real scores for pending predictions and update the store |

## Data Sources

- [Kaggle — International football results](https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017) (historical results, 1872–2026)
- [eloratings.net](https://www.eloratings.net) (scraped Elo ratings)
- [football-data.org](https://www.football-data.org) (live schedule and results, free API)

## Known Limitations

- Elo ratings are not refreshed automatically during the tournament (requires manual re-scraping)
- Home-advantage handling for co-host nations relies on a heuristic (team identity), not the actual match venue — a deliberate choice after observing that pure geography doesn't reflect real crowd support (e.g. Mexico, whose fans travel in large numbers to matches played in the United States)
- No feature based on squad market value or player ratings: the historical data needed (exact lineup per match, over 25 years) isn't reliably available in a structured form
- Past World Cup matches seeded via `seed_store.py` are computed retrospectively, not predicted in real time

## License

MIT — see [LICENSE](LICENSE)

## Author

[![GitHub](https://img.shields.io/badge/GitHub-CR0ZER-blue.svg)](https://github.com/CR0ZER)