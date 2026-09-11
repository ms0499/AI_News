import { useEffect, useMemo, useState } from "react";
import { fetchBenchmarks } from "../api/client";
import type { BenchmarkScore, BenchmarksResponse } from "../api/types";
import StateNotice from "../components/StateNotice";
import "./Benchmarks.css";

const TOP_N = 25;

// One tab per benchmark category. `field` is both the response array key and the
// BenchmarkScore property the primary column reads. Each tab is ranked server-side
// by that metric; every tab additionally shows Latency and Context columns.
type TabKey = "intelligence" | "coding" | "agentic" | "cost" | "speed";

interface Tab {
  key: TabKey;
  label: string;
  metricLabel: string;
  hint: string;
  format: (v: number) => string;
}

function fmtContext(v: number): string {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(v % 1_000_000 ? 1 : 0)}M`;
  if (v >= 1_000) return `${Math.round(v / 1_000)}K`;
  return String(v);
}

const fmtIndex = (v: number) => String(Math.round(v));
const fmtLatency = (v: number) => `${v.toFixed(2)}s`;

// Cost/task spans ~$0.0003 to hundreds, so scale the precision to the magnitude
// rather than rounding sub-cent models to "$0.00".
function fmtCost(v: number): string {
  if (v >= 1) return `$${v.toFixed(2)}`;
  if (v >= 0.01) return `$${v.toFixed(3)}`;
  return `$${v.toFixed(4)}`;
}

const TABS: Tab[] = [
  { key: "intelligence", label: "Intelligence", metricLabel: "Intelligence", hint: "Artificial Analysis Intelligence Index", format: fmtIndex },
  { key: "coding", label: "Coding", metricLabel: "Coding", hint: "Coding Index", format: fmtIndex },
  { key: "agentic", label: "Agentic", metricLabel: "Agentic", hint: "Agentic / tool-use index", format: fmtIndex },
  { key: "cost", label: "Cost", metricLabel: "Cost / task", hint: "USD to run one Artificial Analysis Intelligence Index task (cheapest first)", format: fmtCost },
  { key: "speed", label: "Speed", metricLabel: "Speed (t/s)", hint: "Median output tokens/sec", format: (v) => `${Math.round(v)}` },
];

export default function Benchmarks() {
  const [data, setData] = useState<BenchmarksResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [activeKey, setActiveKey] = useState<TabKey>("intelligence");

  useEffect(() => {
    fetchBenchmarks({ limit: TOP_N })
      .then((res) => {
        setData(res);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  // Only show tabs that actually have rows (AA's free API may not populate every
  // category), and always keep the active tab on a populated one.
  const availableTabs = useMemo(
    () => TABS.filter((t) => (data?.[t.key]?.length ?? 0) > 0),
    [data],
  );

  useEffect(() => {
    if (availableTabs.length && !availableTabs.some((t) => t.key === activeKey)) {
      setActiveKey(availableTabs[0].key);
    }
  }, [availableTabs, activeKey]);

  const activeTab = TABS.find((t) => t.key === activeKey) ?? TABS[0];
  const rows = data?.[activeKey] ?? [];

  // Latency / Context are shown in every tab, but hide either if no model in this
  // tab has the value (so AA-missing metrics don't leave a dead all-"—" column).
  const showLatency = rows.some((m) => m.latency != null);
  const showContext = rows.some((m) => m.context_length != null);

  const empty = status === "ready" && availableTabs.length === 0;
  const fromAA = (data?.source_note || "").toLowerCase().includes("artificial analysis");
  const updated = data?.generated_at ? new Date(data.generated_at).toLocaleDateString() : null;

  return (
    <>
      <div className="page-header">
        <h1>Benchmarks</h1>
        <p>
          Top models per category, ranked from{" "}
          <a href="https://artificialanalysis.ai/models" target="_blank" rel="noreferrer">
            Artificial Analysis
          </a>{" "}
          data. Latency and context window are shown alongside every category.
        </p>
      </div>

      {status === "loading" && <StateNotice kind="loading" message="Loading benchmarks…" />}
      {status === "error" && <StateNotice kind="error" message="Couldn't reach the benchmarks API." />}
      {empty && (
        <StateNotice
          kind="empty"
          message={
            data?.enabled
              ? "No benchmark data yet — run ingestion to generate it."
              : "Benchmarks are off. Set BENCHMARK_ENABLED=true and add an Artificial Analysis API key, then run ingestion."
          }
        />
      )}

      {status === "ready" && availableTabs.length > 0 && (
        <>
          <div className="bench-tabs" role="tablist">
            {availableTabs.map((t) => (
              <button
                key={t.key}
                role="tab"
                aria-selected={t.key === activeKey}
                className={`bench-tab${t.key === activeKey ? " is-active" : ""}`}
                onClick={() => setActiveKey(t.key)}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="bench-table-wrap">
            <table className="bench-table">
              <thead>
                <tr>
                  <th className="bench-th bench-th--rank">#</th>
                  <th className="bench-th bench-th--model">Model</th>
                  <th className="bench-th bench-th--num is-sorted" title={activeTab.hint}>
                    {activeTab.metricLabel}
                  </th>
                  {showLatency && (
                    <th className="bench-th bench-th--num" title="Median time to first token (s)">
                      Latency
                    </th>
                  )}
                  {showContext && (
                    <th className="bench-th bench-th--num" title="Context window (tokens)">
                      Context
                    </th>
                  )}
                </tr>
              </thead>
              <tbody>
                {rows.map((m: BenchmarkScore, i) => (
                  <tr className="bench-row" key={m.id}>
                    <td className="bench-td bench-td--rank">{i + 1}</td>
                    <td className="bench-td bench-td--model">
                      <span className="bench-model">{m.model_name}</span>
                      <span className="bench-model__meta">
                        {m.company && <span className="bench-model__company">{m.company}</span>}
                        {m.is_open_weights != null && (
                          <span
                            className={`bench-badge bench-badge--${m.is_open_weights ? "open" : "closed"}`}
                          >
                            {m.is_open_weights ? "Open" : "Closed"}
                          </span>
                        )}
                      </span>
                    </td>
                    <td className="bench-td bench-td--num is-sorted">
                      {m[activeKey] != null ? activeTab.format(m[activeKey] as number) : "—"}
                    </td>
                    {showLatency && (
                      <td className="bench-td bench-td--num">
                        {m.latency != null ? fmtLatency(m.latency) : "—"}
                      </td>
                    )}
                    {showContext && (
                      <td className="bench-td bench-td--num">
                        {m.context_length != null ? fmtContext(m.context_length) : "—"}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {status === "ready" && data?.source_note && (
        <p className="bench-footer">
          {fromAA ? "Source: " : "AI-generated · "}
          {data.source_note}
          {updated ? ` · updated ${updated}` : ""}
        </p>
      )}
    </>
  );
}
