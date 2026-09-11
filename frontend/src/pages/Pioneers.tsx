import { useEffect, useState } from "react";
import { fetchPioneers } from "../api/client";
import type { Pioneer } from "../api/types";
import StateNotice from "../components/StateNotice";
import "./Pioneers.css";

export default function Pioneers() {
  const [pioneers, setPioneers] = useState<Pioneer[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    fetchPioneers()
      .then((res) => {
        setPioneers(res.pioneers);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  return (
    <>
      <div className="page-header">
        <h1>Pioneers</h1>
        <p>The people whose research and companies built the field of AI as it exists today.</p>
      </div>

      {status === "loading" && <StateNotice kind="loading" message="Loading pioneers…" />}
      {status === "error" && <StateNotice kind="error" message="Couldn't reach the pioneers API." />}
      {status === "ready" && pioneers.length === 0 && (
        <StateNotice kind="empty" message="No pioneers seeded yet." />
      )}

      <div className="pioneer-grid">
        {pioneers.map((pioneer) => (
          <div className="pioneer-card" key={pioneer.id}>
            <div className="pioneer-card__header">
              {pioneer.photo_url ? (
                <img className="pioneer-card__photo" src={pioneer.photo_url} alt={pioneer.name} />
              ) : (
                <div className="pioneer-card__avatar">{pioneer.name.charAt(0)}</div>
              )}
              <div>
                <div className="pioneer-card__name">{pioneer.name}</div>
                <div className="pioneer-card__role">
                  {pioneer.role}
                  {pioneer.company_name && <> · {pioneer.company_name}</>}
                </div>
              </div>
            </div>

            {pioneer.contribution && <p className="pioneer-card__contribution">{pioneer.contribution}</p>}
            {pioneer.bio && <p className="pioneer-card__bio">{pioneer.bio}</p>}

            {pioneer.latest_quote && (
              <blockquote className="pioneer-card__quote">
                <p>“{pioneer.latest_quote}”</p>
                <footer>
                  {pioneer.quote_source_url ? (
                    <a href={pioneer.quote_source_url} target="_blank" rel="noreferrer">
                      {pioneer.quote_source_label || "Source"}
                    </a>
                  ) : (
                    pioneer.quote_source_label
                  )}
                  {pioneer.quote_date && <> · {pioneer.quote_date}</>}
                </footer>
              </blockquote>
            )}

            {pioneer.links.length > 0 && (
              <div className="pioneer-card__links">
                {pioneer.links.map((link) => (
                  <a key={link.url} href={link.url} target="_blank" rel="noreferrer" className="chip">
                    {link.label} ↗
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
