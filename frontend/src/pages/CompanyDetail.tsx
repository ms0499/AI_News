import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchCompany } from "../api/client";
import type { Article, Company } from "../api/types";
import ArticleCard from "../components/ArticleCard";
import StateNotice from "../components/StateNotice";

export default function CompanyDetail() {
  const { slug } = useParams<{ slug: string }>();
  const [company, setCompany] = useState<Company | null>(null);
  const [articles, setArticles] = useState<Article[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    if (!slug) return;
    setStatus("loading");
    fetchCompany(slug)
      .then((res) => {
        setCompany(res.company);
        setArticles(res.recent_articles);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, [slug]);

  if (status === "loading") return <StateNotice kind="loading" message="Loading company…" />;
  if (status === "error" || !company) return <StateNotice kind="error" message="Company not found." />;

  return (
    <>
      <div className="page-header">
        <h1>{company.name}</h1>
        {company.description && <p>{company.description}</p>}
      </div>

      {articles.length === 0 ? (
        <StateNotice kind="empty" message="No recent articles mentioning this company yet." />
      ) : (
        <div className="feed-grid">
          {articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      )}
    </>
  );
}
