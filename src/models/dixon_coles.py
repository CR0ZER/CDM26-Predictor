import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln
import joblib
import math


class DixonColesModel:
    def __init__(self, xi: float = 0.0018, l2_reg: float = 0.001, max_goals: int = 10):
        self.xi = xi
        self.l2_reg = l2_reg
        self.max_goals = max_goals

    def _unpack(self, params, n_teams):
        attack = params[:n_teams]
        defense = params[n_teams:2*n_teams]
        home_adv = params[2*n_teams]
        rho = params[2*n_teams + 1]
        return attack, defense, home_adv, rho

    def _tau(self, x, y, lam, mu, rho):
        if x == 0 and y == 0:
            return 1 - lam * mu * rho
        elif x == 0 and y == 1:
            return 1 + lam * rho
        elif x == 1 and y == 0:
            return 1 + mu * rho
        elif x == 1 and y == 1:
            return 1 - rho
        return 1.0

    def _nll_and_grad(self, params, home_idx, away_idx, x, y, weights, n_teams):
        attack, defense, home_adv, rho = self._unpack(params, n_teams)

        lam = np.exp(home_adv + attack[home_idx] - defense[away_idx])
        mu  = np.exp(attack[away_idx] - defense[home_idx])

        log_lik = (x * np.log(lam) - lam - gammaln(x + 1)) + \
                  (y * np.log(mu)  - mu  - gammaln(y + 1))

        is_00 = (x == 0) & (y == 0)
        is_01 = (x == 0) & (y == 1)
        is_10 = (x == 1) & (y == 0)
        is_11 = (x == 1) & (y == 1)

        tau = np.ones_like(lam)
        tau = np.where(is_00, 1 - lam*mu*rho, tau)
        tau = np.where(is_01, 1 + lam*rho, tau)
        tau = np.where(is_10, 1 + mu*rho, tau)
        tau = np.where(is_11, 1 - rho, tau)
        tau = np.clip(tau, 1e-6, None)

        log_lik += np.log(tau)
        nll = -np.sum(weights * log_lik) + self.l2_reg * (np.sum(attack**2) + np.sum(defense**2))

        dlogtau_dlam = np.zeros_like(lam)
        dlogtau_dmu  = np.zeros_like(mu)
        dlogtau_drho = np.zeros_like(lam)

        dlogtau_dlam = np.where(is_00, -mu*rho/tau, dlogtau_dlam)
        dlogtau_dlam = np.where(is_01, rho/tau, dlogtau_dlam)

        dlogtau_dmu = np.where(is_00, -lam*rho/tau, dlogtau_dmu)
        dlogtau_dmu = np.where(is_10, rho/tau, dlogtau_dmu)

        dlogtau_drho = np.where(is_00, -lam*mu/tau, dlogtau_drho)
        dlogtau_drho = np.where(is_01, lam/tau, dlogtau_drho)
        dlogtau_drho = np.where(is_10, mu/tau, dlogtau_drho)
        dlogtau_drho = np.where(is_11, -1.0/tau, dlogtau_drho)

        G_lam = -weights * (x/lam - 1) - weights * dlogtau_dlam
        G_mu  = -weights * (y/mu - 1)  - weights * dlogtau_dmu
        grad_rho = np.sum(-weights * dlogtau_drho)

        grad_attack  = np.zeros(n_teams)
        grad_defense = np.zeros(n_teams)

        np.add.at(grad_attack, home_idx, G_lam * lam)
        np.add.at(grad_attack, away_idx, G_mu * mu)
        np.add.at(grad_defense, away_idx, -G_lam * lam)
        np.add.at(grad_defense, home_idx, -G_mu * mu)

        grad_attack  += 2 * self.l2_reg * attack
        grad_defense += 2 * self.l2_reg * defense
        grad_home_adv = np.sum(G_lam * lam)

        grad = np.concatenate([grad_attack, grad_defense, [grad_home_adv], [grad_rho]])
        return nll, grad

    def fit(self, df: pd.DataFrame, fit_date: str | None = None) -> "DixonColesModel":
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        self.fit_date_ = pd.to_datetime(fit_date) if fit_date else df["date"].max()

        self.teams_ = sorted(set(df["home_team"]) | set(df["away_team"]))
        self.team_idx_ = {t: i for i, t in enumerate(self.teams_)}
        n_teams = len(self.teams_)

        home_idx = df["home_team"].map(self.team_idx_).values
        away_idx = df["away_team"].map(self.team_idx_).values
        x = df["home_score"].values.astype(float)
        y = df["away_score"].values.astype(float)

        days_ago = (self.fit_date_ - df["date"]).dt.days.values
        weights = np.exp(-self.xi * days_ago)

        x0 = np.concatenate([np.zeros(n_teams), np.zeros(n_teams), [0.2], [0.0]])

        print(f"      Optimisation (gradient analytique) sur {n_teams} équipes, {len(df)} matchs...")
        result = minimize(
            self._nll_and_grad, x0,
            args=(home_idx, away_idx, x, y, weights, n_teams),
            method="L-BFGS-B",
            jac=True,
            options={"maxiter": 1000, "maxfun": 50000, "disp": False},
        )

        self.attack_, self.defense_, self.home_adv_, self.rho_ = self._unpack(result.x, n_teams)
        self.converged_ = result.success
        self.message_ = result.message
        self.n_iter_ = result.nit
        self.nll_ = result.fun
        return self

    def predict_lambdas(self, home_team: str, away_team: str) -> tuple[float, float]:
        avg_attack = float(np.mean(self.attack_))
        avg_defense = float(np.mean(self.defense_))
        a_home = self.attack_[self.team_idx_[home_team]] if home_team in self.team_idx_ else avg_attack
        d_home = self.defense_[self.team_idx_[home_team]] if home_team in self.team_idx_ else avg_defense
        a_away = self.attack_[self.team_idx_[away_team]] if away_team in self.team_idx_ else avg_attack
        d_away = self.defense_[self.team_idx_[away_team]] if away_team in self.team_idx_ else avg_defense
        lam = np.exp(self.home_adv_ + a_home - d_away)
        mu  = np.exp(a_away - d_home)
        return float(lam), float(mu)

    def predict_score_grid(self, home_team: str, away_team: str) -> np.ndarray:
        lam, mu = self.predict_lambdas(home_team, away_team)
        n = self.max_goals + 1
        grid = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                p = (np.exp(-lam) * lam**i / math.factorial(i)) * \
                    (np.exp(-mu) * mu**j / math.factorial(j)) * \
                    self._tau(i, j, lam, mu, self.rho_)
                grid[i, j] = max(p, 0)
        grid /= grid.sum()
        return grid

    def predict_outcome_probs(self, home_team: str, away_team: str) -> tuple[float, float, float]:
        grid = self.predict_score_grid(home_team, away_team)
        n = grid.shape[0]
        p_home = sum(grid[i, j] for i in range(n) for j in range(n) if i > j)
        p_draw = sum(grid[i, i] for i in range(n))
        p_away = sum(grid[i, j] for i in range(n) for j in range(n) if i < j)
        return p_home, p_draw, p_away

    def save(self, path):
        joblib.dump(self, path)

    @staticmethod
    def load(path) -> "DixonColesModel":
        return joblib.load(path)