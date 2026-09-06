import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCompanies } from "../api/client";
import type { Company } from "../api/types";
import StateNotice from "../components/StateNotice";
import "./Companies.css";

export default function Companies() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    fetchCompanies()
      .then((res) => {
        setCompanies(res.companies);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  return (
    <>
      <div className="page-header">
        <h1>Companies</h1>
        <p>Who's building what in AI right now.</p>
      </div>

      {status === "loading" && <StateNotice kind="loading" message="Loading companies…" />}
      {status === "error" && <StateNotice kind="error" message="Couldn't reach the companies API." />}
      {status === "ready" && companies.length === 0 && (
        <StateNotice kind="empty" message="No companies tracked yet — run ingestion to populate this." />
      )}

      <div className="company-grid">
        {companies.map((company) => (
          <Link className="company-card" to={`/companies/${company.slug}`} key={company.id}>
            <div className="company-card__avatar">{company.name.charAt(0)}</div>
            <div className="company-card__name">{company.name}</div>
            {company.description && <p className="company-card__desc">{company.description}</p>}
          </Link>
        ))}
      </div>
    </>
  );
}
