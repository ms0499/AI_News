import { useCallback, useEffect, useState } from "react";
import { fetchFeed } from "../api/client";
import type { Article } from "../api/types";
import ArticleCard from "../components/ArticleCard";
import FilterBar from "../components/FilterBar";
import StateNotice from "../components/StateNotice";

const AUTO_REFRESH_MS = 3 * 60 * 1000;

export default function Feed() {
  const [section, setSection] = useState<string | null>(null);
  const [company, setCompany] = useState<string | undefined>();
  const [topic, setTopic] = useState<string | undefined>();
  const [page, setPage] = useState(1);
  const [articles, setArticles] = useState<Article[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  const load = useCallback(
    async (targetPage: number, replace: boolean) => {
      setStatus((prev) => (replace ? "loading" : prev));
      try {
        const res = await fetchFeed({
          section: section || undefined,
          company,
          topic,
          page: targetPage,
        });
        setArticles((prev) => (replace ? res.articles : [...prev, ...res.articles]));
        setTotal(res.total);
        setStatus("ready");
      } catch {
        setStatus("error");
      }
    },
    [section, company, topic],
  );

  useEffect(() => {
    setPage(1);
    load(1, true);
  }, [load]);

  useEffect(() => {
    const id = setInterval(() => load(1, true), AUTO_REFRESH_MS);
    return () => clearInterval(id);
  }, [load]);

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    load(nextPage, false);
  };

  return (
    <>
      <div className="page-header">
        <h1>AI News Feed</h1>
        <p>Model releases, company moves, and research — pulled from labs, publications, and communities.</p>
      </div>

      <FilterBar
        section={section}
        onSectionChange={(s) => setSection(s)}
        activeFilters={{ company, topic }}
        onClearFilter={(kind) => (kind === "company" ? setCompany(undefined) : setTopic(undefined))}
      />

      {status === "loading" && <StateNotice kind="loading" message="Loading the latest AI news…" />}
      {status === "error" && <StateNotice kind="error" message="Couldn't reach the feed API. Is the backend running?" />}
      {status === "ready" && articles.length === 0 && (
        <StateNotice kind="empty" message="No articles yet — run the ingestion job to pull in the first batch." />
      )}

      {articles.length > 0 && (
        <>
          <div className="feed-grid">
            {articles.map((article) => (
              <ArticleCard
                key={article.id}
                article={article}
                onFilterCompany={setCompany}
                onFilterTopic={setTopic}
              />
            ))}
          </div>
          {articles.length < total && (
            <button className="load-more" onClick={handleLoadMore} disabled={status === "loading"}>
              Load more
            </button>
          )}
        </>
      )}
    </>
  );
}
