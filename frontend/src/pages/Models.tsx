import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchModelReleases } from "../api/client";
import type { ModelGroup, ModelRelease } from "../api/types";
import StateNotice from "../components/StateNotice";
import "./Models.css";

const COLLAPSED_COUNT = 6;
const RECENT_DAYS = 30;

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function formatContext(tokens: number | null): string | null {
  if (!tokens) return null;
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(tokens % 1_000_000 ? 1 : 0)}M ctx`;
  if (tokens >= 1_000) return `${Math.round(tokens / 1_000)}K ctx`;
  return `${tokens} ctx`;
}

function formatPrice(value: number | null): string {
  if (value === null || value === undefined) return "—";
  if (value === 0) return "Free";
  return `$${value >= 1 ? value.toFixed(2) : value.toPrecision(2)}`;
}

const MODALITY_ICON: Record<string, string> = {
  text: "📝",
  image: "🖼️",
  file: "📄",
  audio: "🔊",
  video: "🎬",
};

function isRecent(iso: string | null): boolean {
  if (!iso) return false;
  const days = (Date.now() - new Date(iso).getTime()) / 86_400_000;
  return days <= RECENT_DAYS;
}

function ModelCard({ model }: { model: ModelRelease }) {
  const context = formatContext(model.context_length);
  const iq = model.intelligence_index;
  return (
    <div className="model-card">
      <div className="model-card__top">
        <span className="model-card__name">{model.model_name}</span>
        {iq != null && (
          <span className="model-card__iq" title="Artificial Analysis Intelligence Index (0-100)">
            ★ {Math.round(iq)}
          </span>
        )}
        {model.is_flagship && <span className="chip chip--latest">Latest</span>}
        {!model.is_flagship && isRecent(model.release_date) && <span className="chip chip--new">New</span>}
      </div>

      <div className="model-card__meta">
        <span className="model-card__date">{formatDate(model.release_date)}</span>
        {context && <span className="model-card__pill">{context}</span>}
        {model.modalities.length > 0 && (
          <span className="model-card__pill" title={model.modalities.join(", ")}>
            {model.modalities.map((m) => MODALITY_ICON[m] || "•").join(" ")}
          </span>
        )}
      </div>

      {model.description && <p className="model-card__desc">{model.description}</p>}

      <div className="model-card__footer">
        <div className="model-card__price">
          <span>in {formatPrice(model.input_price)}</span>
          <span className="model-card__price-sep">·</span>
          <span>out {formatPrice(model.output_price)}</span>
          <span className="model-card__price-unit">/1M tok</span>
        </div>
        {model.reference_url && (
          <a className="model-card__link" href={model.reference_url} target="_blank" rel="noreferrer">
            Details ↗
          </a>
        )}
      </div>
    </div>
  );
}

function CompanySection({ group }: { group: ModelGroup }) {
  const [expanded, setExpanded] = useState(false);
  const shown = expanded ? group.models : group.models.slice(0, COLLAPSED_COUNT);
  const hidden = group.models.length - shown.length;

  return (
    <section className="model-group">
      <div className="model-group__head">
        <h2>
          {group.company_slug ? (
            <Link to={`/companies/${group.company_slug}`}>{group.company}</Link>
          ) : (
            group.company
          )}
        </h2>
        <span className="model-group__count">{group.models.length} models</span>
      </div>
      <div className="model-grid">
        {shown.map((m) => (
          <ModelCard key={m.id} model={m} />
        ))}
      </div>
      {hidden > 0 && (
        <button className="model-group__more" onClick={() => setExpanded(true)}>
          Show {hidden} more from {group.company}
        </button>
      )}
      {expanded && group.models.length > COLLAPSED_COUNT && (
        <button className="model-group__more" onClick={() => setExpanded(false)}>
          Show less
        </button>
      )}
    </section>
  );
}

export default function Models() {
  const [groups, setGroups] = useState<ModelGroup[]>([]);
  const [releases, setReleases] = useState<ModelRelease[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [query, setQuery] = useState("");
  const [activeCompany, setActiveCompany] = useState<string | null>(null);

  useEffect(() => {
    fetchModelReleases(undefined, true)
      .then((res) => {
        setGroups(res.groups);
        setReleases(res.releases);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  const latest = useMemo(
    () => releases.filter((r) => r.release_date).slice(0, 8),
    [releases],
  );

  // Highest-rated models across every lab, by the Artificial Analysis
  // Intelligence Index. Empty (and the strip hidden) when AA data isn't present.
  const topRated = useMemo(
    () =>
      releases
        .filter((r) => r.intelligence_index != null)
        .sort((a, b) => (b.intelligence_index ?? 0) - (a.intelligence_index ?? 0))
        .slice(0, 8),
    [releases],
  );

  const filteredGroups = useMemo(() => {
    const q = query.trim().toLowerCase();
    return groups
      .filter((g) => !activeCompany || g.company_slug === activeCompany)
      .map((g) => ({
        ...g,
        models: q
          ? g.models.filter(
              (m) =>
                m.model_name.toLowerCase().includes(q) ||
                (m.description || "").toLowerCase().includes(q),
            )
          : g.models,
      }))
      .filter((g) => g.models.length > 0);
  }, [groups, query, activeCompany]);

  return (
    <>
      <div className="page-header">
        <h1>AI Models</h1>
        <p>
          A live catalog of every major lab's models — latest versions, context windows, and
          pricing, refreshed from the OpenRouter model registry. Intelligence scores (★) are the
          independent Artificial Analysis Intelligence Index, where available.
        </p>
      </div>

      {status === "loading" && <StateNotice kind="loading" message="Loading model catalog…" />}
      {status === "error" && <StateNotice kind="error" message="Couldn't reach the models API." />}
      {status === "ready" && releases.length === 0 && (
        <StateNotice kind="empty" message="No models tracked yet — run ingestion to populate this." />
      )}

      {status === "ready" && releases.length > 0 && (
        <>
          <section className="latest-strip">
            <h2 className="latest-strip__title">🚀 Latest releases</h2>
            <div className="latest-strip__row">
              {latest.map((m) => (
                <div className="latest-chip" key={m.id}>
                  <span className="latest-chip__company">{m.company}</span>
                  <span className="latest-chip__model">{m.model_name}</span>
                  <span className="latest-chip__date">{formatDate(m.release_date)}</span>
                </div>
              ))}
            </div>
          </section>

          {topRated.length > 0 && (
            <section className="latest-strip">
              <h2 className="latest-strip__title">🧠 Smartest models</h2>
              <div className="latest-strip__row">
                {topRated.map((m) => (
                  <div className="latest-chip" key={`iq-${m.id}`}>
                    <span className="latest-chip__company">{m.company}</span>
                    <span className="latest-chip__model">{m.model_name}</span>
                    <span className="latest-chip__date">
                      ★ {Math.round(m.intelligence_index ?? 0)}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}

          <div className="model-controls">
            <input
              className="model-search"
              type="search"
              placeholder="Search models…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <div className="model-filter-chips">
              <button
                className={`chip ${activeCompany === null ? "chip--active" : ""}`}
                onClick={() => setActiveCompany(null)}
              >
                All
              </button>
              {groups.map((g) => (
                <button
                  key={g.company_slug}
                  className={`chip ${activeCompany === g.company_slug ? "chip--active" : ""}`}
                  onClick={() => setActiveCompany(g.company_slug)}
                >
                  {g.company}
                </button>
              ))}
            </div>
          </div>

          {filteredGroups.length === 0 && (
            <StateNotice kind="empty" message="No models match your search." />
          )}
          {filteredGroups.map((g) => (
            <CompanySection key={g.company_slug} group={g} />
          ))}
        </>
      )}
    </>
  );
}
