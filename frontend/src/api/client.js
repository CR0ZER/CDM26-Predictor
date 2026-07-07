const API_BASE_URL = "http://127.0.0.1:8000/api";

export async function getUpcomingMatches() {
  const res = await fetch(`${API_BASE_URL}/matches`, { cache: "no-store" });
  if (!res.ok) throw new Error("Erreur lors de la récupération des matchs");
  return res.json();
}

export async function predictMatch({ home_team, away_team, date, tournament = "FIFA World Cup", neutral = true }) {
  const res = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ home_team, away_team, date, tournament, neutral }),
  });
  if (!res.ok) throw new Error("Erreur lors de la prédiction");
  return res.json();
}

export async function getBacktest() {
  const res = await fetch(`${API_BASE_URL}/backtest`, { cache: "no-store" });
  if (!res.ok) throw new Error("Erreur lors de la récupération du backtest");
  return res.json();
}

export async function refreshBacktest() {
    const res = await fetch(`${API_BASE_URL}/backtest/refresh`, {
        method: "POST",
        cache: "no-store",
    });
    if (!res.ok) throw new Error("Erreur lors du refresh");
    return res.json();
}