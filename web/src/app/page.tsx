"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Database, BarChart3, Activity } from "lucide-react";
import { fetchDashboardStats, DashboardStats } from "@/lib/api";

// Fallback 数据
const fallbackStats = [
  { title: "Total Articles", value: "—", icon: FileText, desc: "Fetched today" },
  { title: "Data Sources", value: "—", icon: Database, desc: "Active feeds" },
  { title: "Reports Generated", value: "—", icon: BarChart3, desc: "This week" },
  { title: "Pipeline Status", value: "Ready", icon: Activity, desc: "Last run: —" },
];

export default function DashboardPage() {
  const [stats, setStats] = useState(fallbackStats);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 尝试从 API 获取统计数据
    fetchDashboardStats()
      .then((data: DashboardStats) => {
        setStats([
          { 
            title: "Total Articles", 
            value: data.total_articles.toLocaleString(), 
            icon: FileText, 
            desc: "Fetched today" 
          },
          { 
            title: "Data Sources", 
            value: data.active_sources.toString(), 
            icon: Database, 
            desc: "Active feeds" 
          },
          { 
            title: "Reports Generated", 
            value: data.total_reports.toString(), 
            icon: BarChart3, 
            desc: "This week" 
          },
          { 
            title: "Pipeline Status", 
            value: "Ready", 
            icon: Activity, 
            desc: data.last_pipeline_run ? `Last run: ${new Date(data.last_pipeline_run).toLocaleDateString()}` : "Last run: —"
          },
        ]);
      })
      .catch(error => {
        console.log("Failed to fetch dashboard stats:", error.message);
        // 保持 fallback 数据
      })
      .finally(() => setLoading(false));
  }, []);
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 pl-60">
        <Header title="Dashboard" />
        <div className="p-6 space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {stats.map((s) => {
              const Icon = s.icon;
              return (
                <Card key={s.title}>
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      {s.title}
                    </CardTitle>
                    <Icon className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{s.value}</div>
                    <p className="text-xs text-muted-foreground">{s.desc}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                No recent pipeline runs. Start the pipeline to see activity here.
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}