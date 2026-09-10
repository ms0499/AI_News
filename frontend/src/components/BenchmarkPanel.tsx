import { useEffect, useMemo, useState } from "react";
import { fetchBenchmarks } from "../api/client";
import type { BenchmarkScore, BenchmarksResponse } from "../api/types";
import "./BenchmarkPanel.css";

type Metric = "intelligence" | "speed" | "cost";

const TABS: { key: Metric; label: string; hint: string }[] = [
  { key: "intelligence", label: "Intelligence", hint: "Composite index — higher is smarter" },
  { key: "speed", label: "Speed", hint: "Output tokens/sec — higher is faster" },
  { key: "cost", label: "Cost / task", hint: "USD per standard task — lower is cheaper" },
];

function metricValue(s: BenchmarkScore, m: Metric): number | null {
  return s[m];
}

function formatValue(v: number, m: Metric): string {
  if (m === "intelligence") return String(Math.round(v));
  if (m === "speed") return `${Math.round(v)} t/s`;
  return v < 1 ? `$${v.toFixed(3)}` : `$${v.toFixed(2)}`;
}

export default function BenchmarkPanel() {
  const [data, setData] = useState<BenchmarksResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [tab, setTab] = useState<Metric>("intelligence");

  useEffect(() => {
    fetchBenchmarks()
      .then((res) => {
        setData(res);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  const rows = data ? data[tab] : [];

  // Normalise bar widths so "longer = better" for every metric: intelligence and
  // speed scale to the max, cost scales to the min (cheapest fills the bar).
  const scale = useMemo(() => {
    const vals = rows.map((r) => metricValue(r, tab)).filter((v): v is number => v != null);
    if (!vals.length) return () => 0;
    const max = Math.max(...vals);
    const min = Math.min(...vals);
    return (v: number) =>
      tab === "cost"
        ? (min > 0 ? (min / v) * 100 : 0)
        : (max > 0 ? (v / max) * 100 : 0);
  }, [rows, tab]);

  const activeTab = TABS.find((t) => t.key === tab)!;
  const empty = status === "ready" && rows.length === 0;

  return (
    <aside className="benchmark-panel">
      <div className="benchmark-panel__header">
        <h2>Model Benchmarks</h2>
        <p>Top 10 models by intelligence, speed &amp; cost</p>
      </div>

      <div className="benchmark-tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={t.key === tab}
            className={`benchmark-tab${t.key === tab ? " is-active" : ""}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <p className="benchmark-panel__hint">{activeTab.hint}</p>

      {status === "loading" && <p className="benchmark-panel__notice">Loading benchmarks…</p>}
      {status === "error" && (
        <p className="benchmark-panel__notice">Couldn't load benchmarks.</p>
      )}
      {empty && (
        <p className="benchmark-panel__notice">
          {data?.enabled
            ? "No benchmark data yet — run ingestion to generate it."
            : "Benchmarks are off. Set BENCHMARK_ENABLED=true and add a model key, then run ingestion."}
        </p>
      )}

      {status === "ready" && rows.length > 0 && (
        <ol className="benchmark-list">
          {rows.map((row, i) => {
            const v = metricValue(row, tab);
            return (
              <li className="benchmark-row" key={`${tab}-${row.id}`} data-rank={i + 1}>
                <div className="benchmark-row__top">
                  <span className="benchmark-row__rank">{i + 1}</span>
                  <span className="benchmark-row__name">
                    {row.model_name}
                    {row.company && <span className="benchmark-row__company">{row.company}</span>}
                  </span>
                  <span className="benchmark-row__score">{v != null ? formatValue(v, tab) : "—"}</span>
                </div>
                <div className="benchmark-row__bar">
                  <span
                    className={`benchmark-row__fill benchmark-row__fill--${tab}`}
                    style={{ width: `${v != null ? scale(v) : 0}%` }}
                  />
                </div>
              </li>
            );
          })}
        </ol>
      )}

      {status === "ready" && data?.source_note && (
        <p className="benchmark-panel__footer">
          AI-generated from web sources · {data.source_note}
        </p>
      )}
    </aside>
  );
}
