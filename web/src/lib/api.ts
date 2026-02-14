const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Article {
  id: number;
  title: string;
  url: string;
  source: string;
  published_at: string;
  summary?: string;
  category?: string;
  importance?: number;
}

export interface Report {
  id: number;
  date: string;
  title: string;
  format: string;
  file_path: string;
  created_at: string;
  article_count?: number;
}

export interface DashboardStats {
  total_articles: number;
  total_reports: number;
  active_sources: number;
  last_pipeline_run?: string;
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE}/api/dashboard/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function fetchReports(limit = 20): Promise<Report[]> {
  const res = await fetch(`${API_BASE}/api/reports?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch reports");
  return res.json();
}

export async function fetchArticles(date?: string, limit = 50): Promise<Article[]> {
  const params = new URLSearchParams();
  if (date) params.set("date", date);
  params.set("limit", String(limit));
  const res = await fetch(`${API_BASE}/api/articles?${params}`);
  if (!res.ok) throw new Error("Failed to fetch articles");
  return res.json();
}

export async function fetchReportContent(reportId: number): Promise<string> {
  const res = await fetch(`${API_BASE}/api/reports/${reportId}/content`);
  if (!res.ok) throw new Error("Failed to fetch report content");
  const data = await res.json();
  return data.content;
}