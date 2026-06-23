function StatCard({ label, value, color = "#3B6FD6" }) {
  const pct = (value * 100).toFixed(1);
  return (
    <div style={{ marginBottom: "1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, fontSize: "0.9rem" }}>
        <span>{label}</span>
        <strong style={{ fontFamily: "var(--font-mono)" }}>{pct}%</strong>
      </div>
      <div style={{ background: "rgba(245,243,236,0.12)", borderRadius: 4, height: 10, width: "100%" }}>
        <div style={{ background: color, height: "100%", width: `${pct}%`, borderRadius: 4 }} />
      </div>
    </div>
  );
}

export default StatCard;