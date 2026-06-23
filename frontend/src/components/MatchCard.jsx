import Flag from "./Flag";
import ResultProbabilities from "./ResultProbabilities";
import ScoreHeatmap from "./ScoreHeatmap";
import StatCard from "./StatCard";

function MatchCard({ match, prediction, isExpanded, onToggle, onPredictSingle }) {
  return (
    <div className="match-card">
      <div className="match-card-header" onClick={onToggle}>
        <span className="match-card-time">{match.time || ""}</span>
        <span className="match-card-badge">{match.group || match.stage}</span>
      </div>

      <div className="match-card-main" onClick={onToggle}>
        <div className="match-card-team home">
          <Flag team={match.home_team} size={32} />
          <span>{match.home_team}</span>
        </div>

        <div className="match-card-score">
          {prediction
            ? `${prediction.most_likely_home_goals} – ${prediction.most_likely_away_goals}`
            : "vs"}
        </div>

        <div className="match-card-team away">
          <span>{match.away_team}</span>
          <Flag team={match.away_team} size={32} />
        </div>

        <span className={`match-card-chevron ${isExpanded ? "open" : ""}`}>›</span>
      </div>

      {isExpanded && (
        <div className="match-card-expanded">
          {!prediction ? (
            <button className="predict-single-btn" onClick={onPredictSingle}>
              Prédire ce match
            </button>
          ) : (
            <div className="panel-grid">
              <div className="panel"><ResultProbabilities prediction={prediction} /></div>
              <div className="panel"><ScoreHeatmap prediction={prediction} /></div>
              <div className="panel panel-full">
                <h3>Statistiques additionnelles</h3>
                <StatCard label="+2.5 buts" value={prediction.p_over_2_5} color="var(--amber)" />
                <StatCard label="Les deux équipes marquent (BTTS)" value={prediction.p_btts} color="var(--home-blue)" />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MatchCard;