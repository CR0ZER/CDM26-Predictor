import { useState, useEffect, useMemo } from "react";
import { getUpcomingMatches, predictMatch } from "./api/client";
import MatchCard from "./components/MatchCard";

function App() {
  const [matches, setMatches] = useState([]);
  const [predictions, setPredictions] = useState({});
  const [expandedId, setExpandedId] = useState(null);
  const [selectedDayIndex, setSelectedDayIndex] = useState(0);
  const [isPredictingDay, setIsPredictingDay] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getUpcomingMatches().then(setMatches).catch((e) => setError(e.message));
  }, []);

  const days = useMemo(() => {
    return [...new Set(matches.map((m) => m.date))].sort();
  }, [matches]);

  const currentDay = days[selectedDayIndex];

  const dayMatches = useMemo(() => {
    return matches
      .filter((m) => m.date === currentDay)
      .sort((a, b) => (a.time || "").localeCompare(b.time || ""));
  }, [matches, currentDay]);

  const formattedDay = currentDay
    ? new Date(currentDay + "T00:00:00").toLocaleDateString("fr-FR", {
        weekday: "long", day: "numeric", month: "long",
      })
    : "";

  const runPrediction = async (match) => {
    try {
      const result = await predictMatch({
        home_team: match.home_team,
        away_team: match.away_team,
        date: match.date,
        neutral: match.neutral,
      });
      setPredictions((prev) => ({ ...prev, [match.id]: result }));
      return result;
    } catch (e) {
      console.error(`Erreur prédiction ${match.home_team}-${match.away_team} :`, e.message);
      return null;
    }
  };

  const handlePredictDay = async () => {
    setIsPredictingDay(true);
    setError(null);
    try {
      await Promise.all(dayMatches.map((m) => runPrediction(m)));
    } finally {
      setIsPredictingDay(false);
    }
  };

  const handleToggleExpand = (matchId) => {
    setExpandedId((prev) => (prev === matchId ? null : matchId));
  };

  return (
    <div className="app-container">
      <div className="app-eyebrow">Florian Huillet</div>
      <h1 className="app-title">Prédicteur Coupe du Monde 2026</h1>

      {error && <p style={{ color: "var(--away-red)" }}>{error}</p>}

      {days.length > 0 && (
        <>
          <div className="day-nav">
            <button onClick={() => setSelectedDayIndex((i) => Math.max(0, i - 1))} disabled={selectedDayIndex === 0}>
              ‹
            </button>
            <span className="day-label">{formattedDay}</span>
            <button onClick={() => setSelectedDayIndex((i) => Math.min(days.length - 1, i + 1))} disabled={selectedDayIndex === days.length - 1}>
              ›
            </button>
          </div>

          <button className="predict-day-btn" onClick={handlePredictDay} disabled={isPredictingDay || dayMatches.length === 0}>
            {isPredictingDay ? (<><span className="spinner" />Calcul en cours…</>) : `Prédire la journée (${dayMatches.length} matchs)`}
          </button>

          <div className="match-list">
            {dayMatches.map((match) => (
              <MatchCard
                key={match.id}
                match={match}
                prediction={predictions[match.id] || null}
                isExpanded={expandedId === match.id}
                onToggle={() => handleToggleExpand(match.id)}
                onPredictSingle={() => runPrediction(match)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default App;