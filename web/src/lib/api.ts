const API_BASE = "http://localhost:8080";

// ============================================================================
// Type Definitions
// ============================================================================

export interface Article {
  id: number;
  title: string;
  url: string;
  source: string;
  published_at: string;
  summary?: string;
  category?: string;
  importance?: number;
  section?: string;
}

export interface Report {
  id: number;
  date: string;
  title: string;
  format: string;
  file_path: string;
  html_path?: string;
  pdf_path?: string;
  created_at: string;
  article_count?: number;
}

export interface DashboardStats {
  total_articles: number;
  total_reports: number;
  active_sources: number;
  last_pipeline_run?: string;
  articles_by_section?: Record<string, number>;
  reports_last_7_days?: number;
}

export interface Source {
  id: number;
  name: string;
  enabled: boolean;
  channel: string;
  source_type: string;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface PipelineRun {
  id: number;
  date: string;
  layers: string[];
  status: string;
  started_at: string;
  finished_at?: string;
  duration_seconds?: number;
  stats?: Record<string, any>;
  error_message?: string;
  current_layer?: string;
  progress_percent: number;
}

export interface Setting {
  key: string;
  value: any;
  description?: string;
}

export interface Template {
  name: string;
  description: string;
  theme: string;
  features: string[];
}

// ============================================================================
// Dashboard API
// ============================================================================

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE}/api/v1/dashboard/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

// ============================================================================
// Reports API
// ============================================================================

export async function fetchReports(limit = 20): Promise<Report[]> {
  const res = await fetch(`${API_BASE}/api/v1/reports/?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch reports");
  return res.json();
}

export async function fetchReportByDate(date: string): Promise<Report> {
  const res = await fetch(`${API_BASE}/api/v1/reports/${date}`);
  if (!res.ok) throw new Error("Failed to fetch report");
  return res.json();
}

export async function fetchReportContent(reportId: number): Promise<string> {
  const res = await fetch(`${API_BASE}/api/v1/reports/${reportId}/content`);
  if (!res.ok) throw new Error("Failed to fetch report content");
  const data = await res.json();
  return data.content;
}

export async function syncReport(date: string): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/api/v1/reports/${date}/sync`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to sync report");
  return res.json();
}

// ============================================================================
// Articles API
// ============================================================================

export async function fetchArticles(date?: string, limit = 50): Promise<Article[]> {
  const params = new URLSearchParams();
  if (date) params.set("date", date);
  params.set("limit", String(limit));
  const res = await fetch(`${API_BASE}/api/v1/articles/?${params}`);
  if (!res.ok) throw new Error("Failed to fetch articles");
  return res.json();
}

// ============================================================================
// Sources API
// ============================================================================

export async function fetchSources(): Promise<Source[]> {
  const res = await fetch(`${API_BASE}/api/v1/sources/`);
  if (!res.ok) throw new Error("Failed to fetch sources");
  return res.json();
}

export async function syncSourcesFromConfig(): Promise<{ message: string; data: { created: number; updated: number } }> {
  const res = await fetch(`${API_BASE}/api/v1/sources/sync-from-config`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to sync sources");
  return res.json();
}

export async function toggleSource(id: number): Promise<Source> {
  const res = await fetch(`${API_BASE}/api/v1/sources/${id}/toggle`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to toggle source");
  return res.json();
}

export async function deleteSource(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete source");
}

export async function createSource(source: Partial<Source>): Promise<Source> {
  const res = await fetch(`${API_BASE}/api/v1/sources/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(source),
  });
  if (!res.ok) throw new Error("Failed to create source");
  return res.json();
}

export async function updateSource(id: number, source: Partial<Source>): Promise<Source> {
  const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(source),
  });
  if (!res.ok) throw new Error("Failed to update source");
  return res.json();
}

// ============================================================================
// Pipeline API
// ============================================================================

export async function runPipeline(layers?: string[], date?: string): Promise<PipelineRun> {
  const res = await fetch(`${API_BASE}/api/v1/pipeline/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      layers: layers || ["fetch", "rank", "analyze", "generate"],
      date,
    }),
  });
  if (!res.ok) throw new Error("Failed to run pipeline");
  return res.json();
}

export async function fetchPipelineStatus(): Promise<PipelineRun | null> {
  const res = await fetch(`${API_BASE}/api/v1/pipeline/status`);
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error("Failed to fetch pipeline status");
  }
  return res.json();
}

export async function fetchPipelineHistory(limit = 20): Promise<PipelineRun[]> {
  const res = await fetch(`${API_BASE}/api/v1/pipeline/history?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch pipeline history");
  return res.json();
}

// ============================================================================
// Settings API
// ============================================================================

export async function fetchSettings(): Promise<Record<string, any>> {
  const res = await fetch(`${API_BASE}/api/v1/settings/`);
  if (!res.ok) throw new Error("Failed to fetch settings");
  return res.json();
}

export async function fetchSetting(key: string): Promise<Setting> {
  const res = await fetch(`${API_BASE}/api/v1/settings/${key}`);
  if (!res.ok) throw new Error("Failed to fetch setting");
  return res.json();
}

export async function updateSetting(key: string, value: any, description?: string): Promise<Setting> {
  const res = await fetch(`${API_BASE}/api/v1/settings/${key}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value, description }),
  });
  if (!res.ok) throw new Error("Failed to update setting");
  return res.json();
}

// ============================================================================
// Templates API
// ============================================================================

export async function fetchTemplates(): Promise<Template[]> {
  const res = await fetch(`${API_BASE}/api/v1/templates`);
  if (!res.ok) throw new Error("Failed to fetch templates");
  return res.json();
}

export async function fetchTemplatePreview(templateName: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/v1/templates/${templateName}/preview`);
  if (!res.ok) throw new Error("Failed to fetch template preview");
  return res.text();
}

export async function updateTemplate(templateName: string): Promise<Setting> {
  const res = await fetch(`${API_BASE}/api/v1/settings/template`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ template_name: templateName }),
  });
  if (!res.ok) throw new Error("Failed to update template");
  return res.json();
}
