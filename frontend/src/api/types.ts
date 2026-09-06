export interface Article {
  id: number;
  title: string;
  url: string;
  author: string | null;
  published_at: string | null;
  summary: string | null;
  image_url: string | null;
  section: "models" | "companies" | "news" | "papers";
  companies: string[];
  models: string[];
  topics: string[];
  source: string | null;
}

export interface FeedResponse {
  articles: Article[];
  page: number;
  page_size: number;
  total: number;
}

export interface Company {
  id: number;
  name: string;
  slug: string;
  logo_url: string | null;
  description: string | null;
}

export interface CompaniesResponse {
  companies: Company[];
}

export interface CompanyDetailResponse {
  company: Company;
  recent_articles: Article[];
}

export interface ModelRelease {
  id: number;
  model_name: string;
  release_date: string | null;
  description: string | null;
  benchmark_links: string[];
  company: string | null;
  company_slug: string | null;
}

export interface ModelReleasesResponse {
  releases: ModelRelease[];
}
