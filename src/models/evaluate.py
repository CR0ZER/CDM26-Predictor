import numpy as np
import math
from sklearn.metrics import log_loss as sk_log_loss


def rps_single(probs: tuple[float, float, float], outcome: int) -> float:
    """
    probs   : (p_home_win, p_draw, p_away_win)
    outcome : 0=away win, 1=draw, 2=home win
    """
    p_away, p_draw, p_home = probs[2], probs[1], probs[0]
    ordered_probs = [p_away, p_draw, p_home]
    e = [0, 0, 0]
    e[outcome] = 1

    cum_p, cum_e, rps = 0.0, 0.0, 0.0
    for i in range(len(ordered_probs) - 1):
        cum_p += ordered_probs[i]
        cum_e += e[i]
        rps += (cum_p - cum_e) ** 2
    return rps / (len(ordered_probs) - 1)

def evaluate_predictions(probs_list, outcomes) -> dict:
    rps_scores = [rps_single(p, o) for p, o in zip(probs_list, outcomes)]
    y_pred = [[p[2], p[1], p[0]] for p in probs_list]
    ll = sk_log_loss(outcomes, y_pred, labels=[0, 1, 2])
    return {"log_loss": ll, "rps_mean": float(np.mean(rps_scores)), "n_matches": len(outcomes)}

def poisson_grid_probs(lam: float, mu: float, max_goals: int = 10) -> np.ndarray:
    n = max_goals + 1
    grid = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            grid[i, j] = (np.exp(-lam) * lam**i / math.factorial(i)) * \
                         (np.exp(-mu) * mu**j / math.factorial(j))
    grid /= grid.sum()
    return grid

def outcome_probs_from_grid(grid: np.ndarray) -> tuple[float, float, float]:
    n = grid.shape[0]
    p_home = sum(grid[i, j] for i in range(n) for j in range(n) if i > j)
    p_draw = sum(grid[i, i] for i in range(n))
    p_away = sum(grid[i, j] for i in range(n) for j in range(n) if i < j)
    return p_home, p_draw, p_away