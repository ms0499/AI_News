import { useEffect, useState } from "react";
import { fetchModelReleases } from "../api/client";
import type { Company, ModelRelease } from "../api/types";
import "./CompanyModelsModal.css";

function formatDate(iso: string | null): string {
  if (!iso) return "Unknown date";
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export default function CompanyModelsModal({
  company,
  onClose,
}: {
  company: Company;
  onClose: () => void;
}) {
  const [releases, setReleases] = useState<ModelRelease[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    setStatus("loading");
    fetchModelReleases(company.slug)
      .then((res) => {
        setReleases(res.releases);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, [company.slug]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div className="model-modal__overlay" onClick={onClose}>
      <div className="model-modal" onClick={(e) => e.stopPropagation()}>
        <div className="model-modal__header">
          <div className="model-modal__title">
            <span className="model-modal__avatar">{company.name.charAt(0)}</span>
            <div>
              <h2>{company.name}</h2>
              {company.description && <p>{company.description}</p>}
            </div>
          </div>
          <button className="model-modal__close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="model-modal__body">
          {status === "loading" && <p className="model-modal__notice">Loading models…</p>}
          {status === "error" && <p className="model-modal__notice">Couldn't load models for this company.</p>}
          {status === "ready" && releases.length === 0 && (
            <p className="model-modal__notice">No models tracked for {company.name} yet.</p>
          )}

          {releases.map((release) => (
            <div className="model-modal__row" key={release.id}>
              <div className="model-modal__row-header">
                <span className="model-modal__model-name">{release.model_name}</span>
                <span className="model-modal__date">{formatDate(release.release_date)}</span>
              </div>
              {release.description && <p className="model-modal__description">{release.description}</p>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
