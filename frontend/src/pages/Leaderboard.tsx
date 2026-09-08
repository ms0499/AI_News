import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchLeaderboard } from "../api/client";
import type { LeaderboardEntry } from "../api/types";
import StateNotice from "../components/StateNotice";
import "./Leaderboard.css";

export default function Leaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    fetchLeaderboard()
      .then((res) => {
        setEntries(res.entries);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  return (
    <>
      <div className="page-header">
        <h1>Leaderboard</h1>
        <p>Community Open-Weights Leaderboard — via Hugging Face.</p>
      </div>

      <div className="leaderboard-disclaimer">
        This tracks community fine-tunes/merges of <strong>open-weight</strong> models scored on
        Hugging Face's archived Open LLM Leaderboard — it will never show frontier closed models
        like GPT, Gemini, or Claude. For "what's the best model right now," see the flagship badges
        on the <Link to="/models">Models</Link> page instead.
      </div>

      {status === "loading" && <StateNotice kind="loading" message="Loading leaderboard…" />}
      {status === "error" && <StateNotice kind="error" message="Couldn't reach the leaderboard API." />}
      {status === "ready" && entries.length === 0 && (
        <StateNotice kind="empty" message="No leaderboard data yet — run ingestion to populate this." />
      )}

      {entries.length > 0 && (
        <div className="leaderboard-list">
          {entries.map((entry) => (
            <div className="leaderboard-row" key={entry.id}>
              <div className="leaderboard-row__rank">#{entry.rank}</div>
              <div className="leaderboard-row__body">
                <div className="leaderboard-row__model">{entry.model_name}</div>
                {entry.organization && (
                  <div className="leaderboard-row__org">{entry.organization}</div>
                )}
              </div>
              <div className="leaderboard-row__score">{entry.score?.toFixed(2)}</div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
