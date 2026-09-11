import { useEffect, useMemo, useState } from "react";
import { fetchBenchmarks } from "../api/client";
import type { BenchmarkScore, BenchmarksResponse } from "../api/types";
import StateNotice from "../components/StateNotice";
import "./Benchmarks.css";

type Metric = "intelligence" | "coding" | "math" | "agentic" | "speed" | "cost";

const TOP_N = 20;

const TABS: { key: Metric; label: string; icon: string; hint: string }[] = [
  { key: "intelligence", label: "Intelligence", icon: "🧠", hint: "Composite intelligence index — higher is smarter" },
  { key: "coding", label: "Coding", icon: "💻", hint: "Coding & software-engineering index — higher is better" },
  { key: "math", label: "Math", icon: "🔢", hint: "Math & quantitative-reasoning index — higher is better" },
  { key: "agentic", label: "Agentic", icon: "🤖", hint: "Agentic tool-use index — higher is better" },
  { key: "speed", label: "Speed", icon: "⚡", hint: "Output tokens/sec — higher is faster" },
  { key: "cost", label: "Cost / task", icon: "💰", hint: "USD for a standard ~10K-in/2K-out task — lower is cheaper" },
];

function metricValue(s: BenchmarkScore, m: Metric): number | null {
  return s[m];
}

function formatValue(v: number, m: Metric): string {
  if (m === "speed") return `${Math.round(v)} t/s`;
  if (m === "cost") return v < 1 ? `$${v.toFixed(3)}` : `$${v.toFixed(2)}`;
  return String(Math.round(v));
}

export default function Benchmarks() {
  const [data, setData] = useState<BenchmarksResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [tab, setTab] = useState<Metric>("intelligence");

  useEffect(() => {
    fetchBenchmarks({ limit: TOP_N, balanced: true })
      .then((res) => {
        setData(res);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  // Coding/math/agentic only populate from the Artificial Analysis source —
  // hide tabs that come back empty rather than showing a dead tab.
  const visibleTabs = useMemo(
    () => TABS.filter((t) => (data?.[t.key]?.length ?? 0) > 0),
    [data],
  );

  useEffect(() => {
    if (visibleTabs.length && !visibleTabs.some((t) => t.key === tab)) {
      setTab(visibleTabs[0].key);
    }
  }, [visibleTabs, tab]);

  const rows = data ? data[tab] : [];
  const openCount = rows.filter((r) => r.is_open_weights === true).length;
  const closedCount = rows.length - openCount;

  // Normalise bar widths so "longer = better": intelligence/coding/math/
  // agentic/speed scale to the max, cost scales to the min (cheapest fills).
  const scale = useMemo(() => {
    const vals = rows.map((r) => metricValue(r, tab)).filter((v): v is number => v != null);
    if (!vals.length) return () => 0;
    const max = Math.max(...vals);
    const min = Math.min(...vals);
    return (v: number) => (tab === "cost" ? (min > 0 ? (min / v) * 100 : 0) : max > 0 ? (v / max) * 100 : 0);
  }, [rows, tab]);

  const activeTab = TABS.find((t) => t.key === tab)!;
  const empty = status === "ready" && rows.length === 0;
  const fromAA = (data?.source_note || "").toLowerCase().includes("artificial analysis");

  // Split into two columns (1-10 / 11-20) on wide screens.
  const half = Math.ceil(rows.length / 2);
  const columns = [rows.slice(0, half), rows.slice(half)];

  return (
    <>
      <div className="page-header">
        <h1>Benchmarks</h1>
        <p>
          Top {TOP_N} models across every scored category — open-weight and closed models both represented,
          ranked separately then merged.
        </p>
      </div>

      <div className="benchmarks-tabs" role="tablist">
        {(visibleTabs.length ? visibleTabs : TABS).map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={t.key === tab}
            className={`benchmarks-tab${t.key === tab ? " is-active" : ""}`}
            onClick={() => setTab(t.key)}
          >
            <span className="benchmarks-tab__icon">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      <div className="benchmarks-subbar">
        <p className="benchmarks-hint">{activeTab.hint}.</p>
        {rows.length > 0 && (
          <div className="benchmarks-legend">
            <span className="benchmarks-legend__item">
              <span className="benchmarks-legend__dot benchmarks-legend__dot--open" />
              Open-weight ({openCount})
            </span>
            <span className="benchmarks-legend__item">
              <span className="benchmarks-legend__dot benchmarks-legend__dot--closed" />
              Closed ({closedCount})
            </span>
          </div>
        )}
      </div>

      {status === "loading" && <StateNotice kind="loading" message="Loading benchmarks…" />}
      {status === "error" && <StateNotice kind="error" message="Couldn't reach the benchmarks API." />}
      {empty && (
        <StateNotice
          kind="empty"
          message={
            data?.enabled
              ? "No benchmark data yet — run ingestion to generate it."
              : "Benchmarks are off. Set BENCHMARK_ENABLED=true and add a model key, then run ingestion."
          }
        />
      )}

      {status === "ready" && rows.length > 0 && (
        <div className="benchmarks-columns">
          {columns.map((col, colIdx) => (
            <ol className="benchmarks-list" key={colIdx} start={colIdx === 0 ? 1 : half + 1}>
              {col.map((row, i) => {
                const rank = colIdx === 0 ? i + 1 : half + i + 1;
                const v = metricValue(row, tab);
                return (
                  <li className="benchmarks-row" key={`${tab}-${row.id}`} data-rank={rank}>
                    <div className="benchmarks-row__top">
                      <span className="benchmarks-row__rank">{rank}</span>
                      <span className="benchmarks-row__name">
                        <span className="benchmarks-row__model">{row.model_name}</span>
                        <span className="benchmarks-row__meta">
                          {row.company && <span className="benchmarks-row__company">{row.company}</span>}
                          <span
                            className={`benchmarks-row__badge benchmarks-row__badge--${
                              row.is_open_weights ? "open" : "closed"
                            }`}
                          >
                            {row.is_open_weights ? "Open" : "Closed"}
                          </span>
                        </span>
                      </span>
                      <span className="benchmarks-row__score">{v != null ? formatValue(v, tab) : "—"}</span>
                    </div>
                    <div className="benchmarks-row__bar">
                      <span
                        className={`benchmarks-row__fill benchmarks-row__fill--${tab}`}
                        style={{ width: `${v != null ? scale(v) : 0}%` }}
                      />
                    </div>
                  </li>
                );
              })}
            </ol>
          ))}
        </div>
      )}

      {status === "ready" && data?.source_note && (
        <p className="benchmarks-footer">
          {fromAA ? "Source: " : "AI-generated from web sources · "}
          {data.source_note}
        </p>
      )}
    </>
  );
}
