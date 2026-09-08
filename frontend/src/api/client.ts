import type {
  CompaniesResponse,
  CompanyDetailResponse,
  FeedResponse,
  LeaderboardResponse,
  ModelReleasesResponse,
  PioneersResponse,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status} ${path}`);
  }
  return res.json() as Promise<T>;
}

export interface FeedFilters {
  section?: string;
  company?: string;
  topic?: string;
  page?: number;
}

export function fetchFeed(filters: FeedFilters = {}): Promise<FeedResponse> {
  const params = new URLSearchParams();
  if (filters.section) params.set("section", filters.section);
  if (filters.company) params.set("company", filters.company);
  if (filters.topic) params.set("topic", filters.topic);
  if (filters.page) params.set("page", String(filters.page));
  const query = params.toString();
  return getJson<FeedResponse>(`/api/feed${query ? `?${query}` : ""}`);
}

export function fetchModelReleases(companySlug?: string): Promise<ModelReleasesResponse> {
  const query = companySlug ? `?company=${encodeURIComponent(companySlug)}` : "";
  return getJson<ModelReleasesResponse>(`/api/models${query}`);
}

export function fetchCompanies(): Promise<CompaniesResponse> {
  return getJson<CompaniesResponse>("/api/companies");
}

export function fetchCompany(slug: string): Promise<CompanyDetailResponse> {
  return getJson<CompanyDetailResponse>(`/api/companies/${encodeURIComponent(slug)}`);
}

export function fetchPioneers(): Promise<PioneersResponse> {
  return getJson<PioneersResponse>("/api/pioneers");
}

export function fetchLeaderboard(): Promise<LeaderboardResponse> {
  return getJson<LeaderboardResponse>("/api/leaderboard");
}
