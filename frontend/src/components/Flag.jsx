import { getFlagUrl } from "../utils/flags";

function Flag({ team, size = 28 }) {
  const url = getFlagUrl(team, 80);
  if (!url) {
    return <span style={{ width: size, height: size * 0.75, display: "inline-block" }} />;
  }
  return (
    <img
      src={url}
      alt={team}
      style={{ width: size, height: size * 0.75, objectFit: "cover", borderRadius: 2, border: "1px solid rgba(245,243,236,0.2)" }}
    />
  );
}

export default Flag;