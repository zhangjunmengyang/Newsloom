"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Database, BarChart3, Activity, TrendingUp, AlertCircle } from "lucide-react";
import { fetchDashboardStats, fetchReports, Report } from "@/lib/api";
import Link from "next/link";

export default function DashboardPage() {
  const [stats, setStats] = useState({
    total_articles: 0,
    total_reports: 0,
    active_sources: 0,
    last_pipeline_run: "",
    reports_last_7_days: 0,
  });
  const [recentReports, setRecentReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [dashboardData, reportsData] = await Promise.all([
          fetchDashboardStats(),
          fetchReports(5),
        ]);
        setStats(dashboardData);
        setRecentReports(reportsData);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const statCards = [
    {
      title: "Total Articles",
      value: stats.total_articles.toLocaleString(),
      icon: FileText,
      desc: "Collected in database",
    },
    {
      title: "Data Sources",
      value: stats.active_sources.toString(),
      icon: Database,
      desc: "Active feeds",
    },
    {
      title: "Reports Generated",
      value: stats.total_reports.toString(),
      icon: BarChart3,
      desc: "All time",
    },
    {
      title: "Recent Activity",
      value: stats.reports_last_7_days?.toString() || "0",
      icon: TrendingUp,
      desc: "Last 7 days",
    },
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 pl-60">
        <Header title="Dashboard" />
        <div className="p-6 space-y-6">
          {/* Stats Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {statCards.map((s) => {
              const Icon = s.icon;
              return (
                <Card key={s.title} className="card-hover">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      {s.title}
                    </CardTitle>
                    <Icon className="h-5 w-5 text-primary" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{s.value}</div>
                    <p className="text-xs text-muted-foreground mt-1">{s.desc}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Recent Reports */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Recent Reports</CardTitle>
                <Link href="/reports">
                  <Badge variant="outline" className="cursor-pointer hover:bg-accent">
                    View All
                  </Badge>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-sm text-muted-foreground">Loading...</p>
              ) : recentReports.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                  <FileText className="h-12 w-12 mb-3 opacity-50" />
                  <p className="text-sm">No reports generated yet</p>
                  <p className="text-xs mt-1">Run the pipeline to create your first report</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {recentReports.map((report) => (
                    <Link key={report.id} href={`/reports`}>
                      <div className="flex items-center justify-between p-3 rounded-lg border border-border hover:border-primary/30 transition-colors cursor-pointer">
                        <div className="flex items-center gap-3">
                          <FileText className="h-4 w-4 text-primary" />
                          <div>
                            <p className="text-sm font-medium">{report.title}</p>
                            <p className="text-xs text-muted-foreground">
                              {new Date(report.date).toLocaleDateString()} • {report.article_count || 0} articles
                            </p>
                          </div>
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          {report.format}
                        </Badge>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Source Health */}
          <Card>
            <CardHeader>
              <CardTitle>Source Health</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg border" 
                     style={{
                       backgroundColor: "hsl(var(--chart-3) / 0.1)",
                       borderColor: "hsl(var(--chart-3) / 0.2)"
                     }}>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full" style={{ backgroundColor: "hsl(var(--chart-3))" }} />
                    <span className="text-sm font-medium">All sources operational</span>
                  </div>
                  <Badge variant="outline" 
                         style={{
                           backgroundColor: "hsl(var(--chart-3) / 0.1)",
                           color: "hsl(var(--chart-3))",
                           borderColor: "hsl(var(--chart-3) / 0.2)"
                         }}>
                    {stats.active_sources} active
                  </Badge>
                </div>
                {stats.last_pipeline_run && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground px-3">
                    <Activity className="h-3 w-3" />
                    <span>Last pipeline run: {new Date(stats.last_pipeline_run).toLocaleString()}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}