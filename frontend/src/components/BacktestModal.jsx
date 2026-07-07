import { useState, useEffect } from "react";
import { getBacktest, refreshBacktest } from "../api/client";
import Flag from "./Flag";

function MetricCard({ label, value, sub }) {
    return (
        <div style={{
            background: "var(--pitch-dark)",
            border: "1px solid rgba(245,243,236,0.1)",
            borderTop: "2px solid var(--amber)",
            borderRadius: 4,
            padding: "1rem 1.25rem",
            textAlign: "center",
            flex: 1,
        }}>
            <div style={{
                fontFamily: "var(--font-mono)",
                fontSize: "2rem",
                fontWeight: 600,
                color: "var(--amber)",
            }}>
                {value}
            </div>
            <div style={{
                fontFamily: "var(--font-body)",
                fontSize: "0.85rem",
                color: "var(--chalk)",
                marginTop: 4,
            }}>
                {label}
            </div>
            {sub && (
                <div style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.75rem",
                    color: "var(--sage)",
                    marginTop: 4,
                }}>
                    {sub}
                </div>
            )}
        </div>
    );
}

function MatchRow({ match }) {
    const outcomeColor = match.outcome_correct ? "#16a34a" : "#D14B4B";
    const exactBg = match.exact_score_correct ? "#16a34a" : "rgba(245,243,236,0.1)";
    const exactColor = match.exact_score_correct ? "#fff" : "var(--sage)";

    return (
        <div style={{
            display: "grid",
            gridTemplateColumns: "80px 1fr 130px 1fr 70px 70px",
            alignItems: "center",
            gap: "0.5rem",
            padding: "0.6rem 0.75rem",
            borderBottom: "1px solid rgba(245,243,236,0.06)",
        }}>
            <span style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.72rem",
                color: "var(--sage)",
            }}>
                {match.date}
            </span>

            <div style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-end",
                gap: 6,
                fontFamily: "var(--font-body)",
                fontSize: "0.82rem",
            }}>
                <span>{match.home_team}</span>
                <Flag team={match.home_team} size={18} />
            </div>

            <div style={{
                display: "flex",
                gap: 8,
                justifyContent: "center",
                alignItems: "flex-end",
            }}>
                <div style={{ textAlign: "center" }}>
                    <div style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.6rem",
                        color: "var(--sage)",
                        marginBottom: 2,
                        letterSpacing: "0.05em",
                    }}>
                        RÉEL
                    </div>
                    <div style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "1rem",
                        fontWeight: 700,
                        color: "var(--chalk)",
                    }}>
                        {match.actual_home}–{match.actual_away}
                    </div>
                </div>

                <div style={{
                    color: "var(--sage)",
                    fontSize: "0.7rem",
                    paddingBottom: 3,
                }}>
                    vs
                </div>

                <div style={{ textAlign: "center" }}>
                    <div style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.6rem",
                        color: "var(--amber)",
                        marginBottom: 2,
                        letterSpacing: "0.05em",
                    }}>
                        PRÉDIT
                    </div>
                    <div style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "1rem",
                        fontWeight: 400,
                        color: "var(--amber)",
                        opacity: 0.75,
                    }}>
                        {match.predicted_home}–{match.predicted_away}
                    </div>
                </div>
            </div>

            <div style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                fontFamily: "var(--font-body)",
                fontSize: "0.82rem",
            }}>
                <Flag team={match.away_team} size={18} />
                <span>{match.away_team}</span>
            </div>

            <div style={{ textAlign: "center" }}>
                <span style={{
                    background: outcomeColor,
                    color: "#fff",
                    borderRadius: 3,
                    padding: "2px 8px",
                    fontSize: "0.72rem",
                    fontFamily: "var(--font-mono)",
                }}>
                    {match.outcome_correct ? "✓" : "✗"}
                </span>
            </div>

            <div style={{ textAlign: "center" }}>
                <span style={{
                    background: exactBg,
                    color: exactColor,
                    borderRadius: 3,
                    padding: "2px 8px",
                    fontSize: "0.72rem",
                    fontFamily: "var(--font-mono)",
                }}>
                    {match.exact_score_correct ? "✓" : "✗"}
                </span>
            </div>
        </div>
    );
}

function BacktestModal({ onClose }) {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [isRefreshing, setIsRefreshing] = useState(false);

    const handleRefresh = async () => {
        setIsRefreshing(true);
        try {
            const result = await refreshBacktest();
            setData(result.stats);
        } catch (e) {
            setError(e.message);
        } finally {
            setIsRefreshing(false);
        }
    };

    useEffect(() => {
        getBacktest().then(setData).catch((e) => setError(e.message));
    }, []);

    return (
        <div
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
            style={{
                position: "fixed",
                inset: 0,
                background: "rgba(0,0,0,0.75)",
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "center",
                zIndex: 1000,
                padding: "2rem 1rem",
                overflowY: "auto",
            }}
        >
            <div style={{
                background: "var(--pitch-darker)",
                border: "1px solid rgba(245,243,236,0.1)",
                borderRadius: 6,
                width: "100%",
                maxWidth: 860,
                padding: "1.5rem",
            }}>
                <div style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "1.5rem",
                }}>
                    <div>
                        <div className="app-eyebrow" style={{ marginBottom: 4 }}>
                            Évaluation du modèle
                        </div>
                        <h2 style={{
                            margin: 0,
                            fontFamily: "var(--font-display)",
                            fontSize: "1.3rem",
                        }}>
                            Performances — CdM 2026
                        </h2>
                    </div>

                    
                    
                    <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
                        <button
                            onClick={handleRefresh}
                            disabled={isRefreshing}
                            style={{
                                background: "transparent",
                                border: "1px solid var(--amber)",
                                color: "var(--amber)",
                                borderRadius: 4,
                                padding: "0.4rem 0.8rem",
                                cursor: "pointer",
                                fontFamily: "var(--font-mono)",
                                fontSize: "0.8rem",
                            }}
                        >
                            {isRefreshing
                                ? <><span className="spinner" />Mise à jour…</>
                                : "Mettre à jour ↻"
                            }
                        </button>
                        <button onClick={onClose} style={{
                            background: "transparent",
                            border: "1px solid var(--sage)",
                            color: "var(--chalk)",
                            borderRadius: 4,
                            padding: "0.4rem 0.8rem",
                            cursor: "pointer",
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.8rem",
                        }}>
                            Fermer ✕
                        </button>
                    </div>
                </div>

                {error && (
                    <p style={{ color: "var(--away-red)" }}>{error}</p>
                )}

                {!data && !error && (
                    <p style={{
                        color: "var(--sage)",
                        fontFamily: "var(--font-mono)",
                    }}>
                        Chargement…
                    </p>
                )}

                {data && (
                    <>
                        <div style={{
                            display: "flex",
                            gap: "1rem",
                            marginBottom: "1.5rem",
                        }}>
                            <MetricCard
                                label="Matchs évalués"
                                value={data.n_matches}
                                sub={`Mis à jour le ${new Date(data.generated_at).toLocaleDateString("fr-FR")}`}
                            />
                            <MetricCard
                                label="Résultat correct"
                                value={`${(data.outcome_accuracy * 100).toFixed(1)}%`}
                                sub={`${data.outcome_correct}/${data.n_matches} matchs`}
                            />
                            <MetricCard
                                label="Score exact"
                                value={`${(data.exact_score_accuracy * 100).toFixed(1)}%`}
                                sub={`${data.exact_score_correct}/${data.n_matches} matchs`}
                            />
                        </div>

                        <div style={{
                            display: "grid",
                            gridTemplateColumns: "80px 1fr 130px 1fr 70px 70px",
                            gap: "0.5rem",
                            padding: "0.5rem 0.75rem",
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.72rem",
                            color: "var(--sage)",
                            borderBottom: "1px solid rgba(245,243,236,0.15)",
                            marginBottom: 4,
                        }}>
                            <span>Date</span>
                            <span style={{ textAlign: "right" }}>Domicile</span>
                            <span style={{ textAlign: "center" }}>Réel vs Prédit</span>
                            <span>Extérieur</span>
                            <span style={{ textAlign: "center" }}>Résultat</span>
                            <span style={{ textAlign: "center" }}>Score</span>
                        </div>

                        <div style={{ maxHeight: "55vh", overflowY: "auto" }}>
                            {data.matches.map((m, i) => (
                                <MatchRow key={i} match={m} />
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}

export default BacktestModal;