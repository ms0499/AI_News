import type { Article } from "../api/types";
import "./ArticleCard.css";

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

const SECTION_LABEL: Record<Article["section"], string> = {
  models: "Model",
  companies: "Company",
  news: "News",
  papers: "Paper",
  funding: "Funding",
  features: "Feature",
};

interface Props {
  article: Article;
  onFilterCompany?: (company: string) => void;
  onFilterTopic?: (topic: string) => void;
}

export default function ArticleCard({ article, onFilterCompany, onFilterTopic }: Props) {
  return (
    <a className="card" href={article.url} target="_blank" rel="noreferrer">
      <div className="card__top">
        <span className={`card__section card__section--${article.section}`}>
          {SECTION_LABEL[article.section]}
        </span>
        <span className="card__meta">
          {article.source}
          {article.published_at ? ` · ${timeAgo(article.published_at)}` : ""}
        </span>
      </div>

      <h3 className="card__title">{article.title}</h3>

      {article.summary && <p className="card__summary">{article.summary}</p>}

      {(article.companies.length > 0 || article.models.length > 0 || article.topics.length > 0) && (
        <div className="card__tags">
          {article.companies.map((c) => (
            <span
              key={`c-${c}`}
              className="chip chip--company"
              onClick={(e) => {
                e.preventDefault();
                onFilterCompany?.(c);
              }}
            >
              {c}
            </span>
          ))}
          {article.models.map((m) => (
            <span key={`m-${m}`} className="chip">
              {m}
            </span>
          ))}
          {article.topics.map((t) => (
            <span
              key={`t-${t}`}
              className="chip"
              onClick={(e) => {
                e.preventDefault();
                onFilterTopic?.(t);
              }}
            >
              #{t}
            </span>
          ))}
        </div>
      )}
    </a>
  );
}
