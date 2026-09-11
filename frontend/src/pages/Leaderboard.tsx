import { useEffect, useState } from "react";
import { fetchLeaderboard } from "../api/client";
import type { LeaderboardEntry } from "../api/types";
import StateNotice from "../components/StateNotice";
import "./Leaderboard.css";

type Tab = "aa-open" | "aa-closed";

const TABS: { key: Tab; label: string; hint: string }[] = [
  {
    key: "aa-open",
    label: "Open Models",
    hint: "Open-weight models (Llama, Qwen, DeepSeek, ...), ranked by Artificial Analysis Intelligence Index",
  },
  {
    key: "aa-closed",
    label: "Closed Models",
    hint: "Closed/API-only models (GPT, Claude, Gemini, ...), ranked by Artificial Analysis Intelligence Index",
  },
];

export default function Leaderboard() {
  const [tab, setTab] = useState<Tab>("aa-open");
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    setStatus("loading");
    fetchLeaderboard(tab)
      .then((res) => {
        setEntries(res.entries);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, [tab]);

  const activeTab = TABS.find((t) => t.key === tab)!;

  return (
    <>
      <div className="page-header">
        <h1>Model Leaderboard</h1>
        <p>The best models right now, open and closed — ranked by Artificial Analysis's Intelligence Index.</p>
      </div>

      <div className="leaderboard-tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={t.key === tab}
            className={`leaderboard-tab${t.key === tab ? " is-active" : ""}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="leaderboard-disclaimer">{activeTab.hint}.</div>

      {status === "loading" && <StateNotice kind="loading" message="Loading leaderboard…" />}
      {status === "error" && <StateNotice kind="error" message="Couldn't reach the leaderboard API." />}
      {status === "ready" && entries.length === 0 && (
        <StateNotice
          kind="empty"
          message="No leaderboard data yet — enable BENCHMARK_ENABLED and an Artificial Analysis API key, then run ingestion."
        />
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
                {entry.score != null ? Math.round(entry.score) : ""}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
