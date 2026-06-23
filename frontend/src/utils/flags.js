export const FLAG_CODES = {
  Mexico: "mx", "South Africa": "za", "South Korea": "kr", Czechia: "cz",
  Canada: "ca", "Bosnia and Herzegovina": "ba", Qatar: "qa", "United States": "us",
  Australia: "au", Scotland: "gb-sct", Morocco: "ma", Brazil: "br",
  Haiti: "ht", Turkey: "tr", Paraguay: "py", Netherlands: "nl",
  Sweden: "se", Germany: "de", "Ivory Coast": "ci", Ecuador: "ec",
  "Curaçao": "cw", Tunisia: "tn", Japan: "jp", Spain: "es",
  "Saudi Arabia": "sa", Belgium: "be", Iran: "ir", Uruguay: "uy",
  "Cape Verde": "cv", "New Zealand": "nz", Egypt: "eg", Argentina: "ar",
  Austria: "at", France: "fr", Iraq: "iq", Norway: "no",
  Senegal: "sn", Jordan: "jo", Algeria: "dz", Portugal: "pt",
  Uzbekistan: "uz", England: "gb-eng", Ghana: "gh", Panama: "pa",
  Croatia: "hr", Colombia: "co", "DR Congo": "cd", Switzerland: "ch",
};

export function getFlagUrl(teamName, width = 80) {
  const code = FLAG_CODES[teamName];
  if (!code) return null;
  return `https://flagcdn.com/w${width}/${code}.png`;
}