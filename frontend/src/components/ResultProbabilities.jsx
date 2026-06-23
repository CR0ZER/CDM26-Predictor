import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

const COLORS = ["#3B6FD6", "#8FAE9C", "#D14B4B"];

function ResultProbabilities({ prediction }) {
  const data = [
    { name: prediction.home_team, value: prediction.p_home_win * 100 },
    { name: "Nul", value: prediction.p_draw * 100 },
    { name: prediction.away_team, value: prediction.p_away_win * 100 },
  ];

  return (
    <div>
      <h3>Résultat (1X2)</h3>
      <div style={{ width: "100%", height: 220 }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90}>
              {data.map((entry, index) => (
                <Cell key={index} fill={COLORS[index]} stroke="#082C21" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => `${value.toFixed(1)}%`}
              contentStyle={{ background: "#082C21", border: "1px solid #8FAE9C", borderRadius: 4 }}
              itemStyle={{ color: "#F5F3EC" }}
              labelStyle={{ color: "#F5F3EC" }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: "flex", justifyContent: "space-around", marginTop: "0.5rem", fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>
        {data.map((d, i) => (
          <div key={i} style={{ textAlign: "center" }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: COLORS[i], margin: "0 auto 4px" }} />
            <div>{d.name}</div>
            <div style={{ fontWeight: 600 }}>{d.value.toFixed(1)}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ResultProbabilities;