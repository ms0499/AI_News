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
        <h1>Trending Open Models</h1>
        <p>What the open-source AI community is building with right now — live from Hugging Face.</p>
      </div>

      <div className="leaderboard-disclaimer">
        Ranked by Hugging Face's live <strong>trending</strong> score, so it reflects momentum in the
        <strong> open-weight</strong> community this week — not a fixed quality benchmark, and it
        won't include closed models like GPT, Gemini, or Claude. For each lab's current best model,
        pricing, and context window, see the <Link to="/models">Models</Link> page.
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
              <div className="leaderboard-row__score">
                {entry.score != null ? `🔥 ${Math.round(entry.score)}` : ""}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
