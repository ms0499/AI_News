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
          <div className="company-box" key={company.id}>
            <Link className="company-box__header" to={`/companies/${company.slug}`}>
              <div className="company-box__avatar">{company.name.charAt(0)}</div>
              <div>
                <div className="company-box__name">{company.name}</div>
                {company.description && <p className="company-box__desc">{company.description}</p>}
              </div>
            </Link>

            <div className="company-box__news">
              {company.recent_articles && company.recent_articles.length > 0 ? (
                company.recent_articles.map((article) => (
                  <a
                    className="company-box__news-item"
                    href={article.url}
                    target="_blank"
                    rel="noreferrer"
                    key={article.id}
                  >
                    {article.title}
                  </a>
                ))
              ) : (
                <p className="company-box__news-empty">No recent coverage yet.</p>
              )}
            </div>

            <Link className="company-box__more" to={`/companies/${company.slug}`}>
              More from {company.name} →
            </Link>
          </div>
        ))}
      </div>
    </>
  );
}
