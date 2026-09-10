export interface Article {
  id: number;
  title: string;
  url: string;
  author: string | null;
  published_at: string | null;
  summary: string | null;
  image_url: string | null;
  section: "models" | "companies" | "news" | "papers" | "funding" | "features";
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
  recent_articles?: Article[];
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
  is_flagship: boolean;
  catalog_key: string | null;
  context_length: number | null;
  input_price: number | null;
  output_price: number | null;
  modalities: string[];
  knowledge_cutoff: string | null;
  reference_url: string | null;
  intelligence_index: number | null;
}

export interface ModelGroup {
  company: string | null;
  company_slug: string;
  models: ModelRelease[];
}

export interface ModelReleasesResponse {
  releases: ModelRelease[];
  groups: ModelGroup[];
}

export interface PioneerLink {
  label: string;
  url: string;
}

export interface Pioneer {
  id: number;
  slug: string;
  name: string;
  role: string | null;
  company_name: string | null;
  contribution: string | null;
  bio: string | null;
  photo_url: string | null;
  links: PioneerLink[];
}

export interface PioneersResponse {
  pioneers: Pioneer[];
}

export interface LeaderboardEntry {
  id: number;
  rank: number;
  model_name: string;
  organization: string | null;
  score: number | null;
  fetched_at: string | null;
}

export interface LeaderboardResponse {
  source: string;
  entries: LeaderboardEntry[];
}

export interface BenchmarkScore {
  id: number;
  model_name: string;
  company: string | null;
  intelligence: number | null;
  speed: number | null;
  cost: number | null;
  coding: number | null;
  math: number | null;
  agentic: number | null;
}

export interface BenchmarksResponse {
  enabled: boolean;
  generated_at: string | null;
  source_note: string | null;
  intelligence: BenchmarkScore[];
  coding: BenchmarkScore[];
  math: BenchmarkScore[];
  agentic: BenchmarkScore[];
  speed: BenchmarkScore[];
  cost: BenchmarkScore[];
}
