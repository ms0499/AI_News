import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchModelReleases } from "../api/client";
import type { ModelRelease } from "../api/types";
import StateNotice from "../components/StateNotice";
import "./Models.css";

function formatDate(iso: string | null): string {
  if (!iso) return "Unknown date";
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export default function Models() {
  const [releases, setReleases] = useState<ModelRelease[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    fetchModelReleases()
      .then((res) => {
        setReleases(res.releases);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  return (
    <>
      <div className="page-header">
        <h1>Model Releases</h1>
        <p>New models and major updates, tracked by company as they're announced.</p>
      </div>

      {status === "loading" && <StateNotice kind="loading" message="Loading model releases…" />}
      {status === "error" && <StateNotice kind="error" message="Couldn't reach the models API." />}
      {status === "ready" && releases.length === 0 && (
        <StateNotice kind="empty" message="No model releases tracked yet — run ingestion to populate this." />
      )}

      <div className="release-list">
        {releases.map((release) => (
          <div className="release-row" key={release.id}>
            <div className="release-row__date">{formatDate(release.release_date)}</div>
            <div className="release-row__body">
              <div className="release-row__title">
                {release.company_slug ? (
                  <Link to={`/companies/${release.company_slug}`} className="release-row__company">
                    {release.company}
                  </Link>
                ) : (
                  <span className="release-row__company">{release.company}</span>
                )}
                <span className="release-row__model">{release.model_name}</span>
                {release.is_flagship && <span className="chip chip--active">★ Flagship</span>}
              </div>
              {release.description && <p className="release-row__description">{release.description}</p>}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
