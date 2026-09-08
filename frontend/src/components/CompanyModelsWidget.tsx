import { useEffect, useState } from "react";
import { fetchCompanies } from "../api/client";
import type { Company } from "../api/types";
import CompanyModelsModal from "./CompanyModelsModal";
import "./CompanyModelsWidget.css";

export default function CompanyModelsWidget() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [activeCompany, setActiveCompany] = useState<Company | null>(null);

  useEffect(() => {
    fetchCompanies()
      .then((res) => {
        setCompanies(res.companies);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  return (
    <aside className="model-widget">
      <div className="model-widget__header">
        <h2>AI Companies</h2>
        <p>Tap a company to see its models</p>
      </div>

      {status === "loading" && <p className="model-widget__notice">Loading…</p>}
      {status === "error" && <p className="model-widget__notice">Couldn't load companies.</p>}
      {status === "ready" && companies.length === 0 && (
        <p className="model-widget__notice">No companies tracked yet.</p>
      )}

      <ul className="model-widget__list">
        {companies.map((company) => (
          <li key={company.id}>
            <button className="model-widget__item" onClick={() => setActiveCompany(company)}>
              <span className="model-widget__avatar">{company.name.charAt(0)}</span>
              <span className="model-widget__name">{company.name}</span>
            </button>
          </li>
        ))}
      </ul>

      {activeCompany && (
        <CompanyModelsModal company={activeCompany} onClose={() => setActiveCompany(null)} />
      )}
    </aside>
  );
}
