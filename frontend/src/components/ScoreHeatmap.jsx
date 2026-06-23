function ScoreHeatmap({ prediction }) {
  const grid = prediction.score_grid;
  const maxVal = Math.max(...grid.flat());

  const getColor = (value) => {
    const intensity = value / maxVal;
    const alpha = 0.15 + intensity * 0.85;
    return `rgba(59, 111, 214, ${alpha})`;
  };

  const cellStyle = {
    width: 48,
    height: 48,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 11,
    fontFamily: "var(--font-mono)",
    color: "#F5F3EC",
    border: "1px solid #0B3D2E",
  };

  return (
    <div>
      <h3>Grille des scores exacts</h3>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "0.75rem", fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#3B6FD6" }} />
          {prediction.home_team}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#D14B4B" }} />
          {prediction.away_team}
        </div>
      </div>

      <div style={{ display: "inline-block" }}>
        <div style={{ display: "flex" }}>
          <div style={{ width: 36 }} />
          {grid[0].map((_, j) => (
            <div key={j} style={{ ...cellStyle, height: 26, border: "none", color: "#D14B4B", fontWeight: 700 }}>
              {j}
            </div>
          ))}
        </div>

        {grid.map((row, i) => (
          <div key={i} style={{ display: "flex" }}>
            <div style={{ width: 36, height: 48, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-mono)", color: "#3B6FD6", fontWeight: 700 }}>
              {i}
            </div>
            {row.map((value, j) => (
              <div key={j} style={{ ...cellStyle, background: getColor(value) }}>
                {(value * 100).toFixed(1)}%
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ScoreHeatmap;