"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { FileText, Calendar, BarChart } from "lucide-react";
import { fetchReports, fetchReportContent, Report } from "@/lib/api";

// Mock 数据作为 fallback
const mockReports: Report[] = [
  {
    id: 1,
    date: "2026-02-15",
    title: "Daily Intelligence Brief",
    format: "markdown",
    file_path: "/reports/2026-02-15.md",
    created_at: "2026-02-15T08:00:00Z",
    article_count: 12
  },
  {
    id: 2,
    date: "2026-02-14",
    title: "Weekly Tech Roundup",
    format: "markdown",
    file_path: "/reports/2026-02-14.md",
    created_at: "2026-02-14T08:00:00Z",
    article_count: 28
  },
  {
    id: 3,
    date: "2026-02-13",
    title: "Market Analysis Summary",
    format: "markdown",
    file_path: "/reports/2026-02-13.md",
    created_at: "2026-02-13T08:00:00Z",
    article_count: 15
  }
];

const mockContent: { [key: number]: string } = {
  1: `# Daily Intelligence Brief
## February 15, 2026

### Tech News
- **AI Breakthrough**: New language model shows 40% improvement in reasoning tasks
- **Crypto Update**: Bitcoin reaches new resistance at $85k
- **Cloud Wars**: AWS announces quantum computing service

### Key Articles
1. **"The Future of AI Reasoning"** - TechCrunch
   - Summary: Researchers demonstrate significant improvements in logical reasoning capabilities
   - Impact: High
   - Category: AI/ML

2. **"Quantum Computing Goes Mainstream"** - Wired
   - Summary: Major cloud providers racing to offer quantum services
   - Impact: Medium
   - Category: Cloud/Infrastructure

### Market Insights
- Tech stocks up 2.3% on AI news
- Quantum computing sector sees 15% surge
- Crypto market cap reaches $2.8T

### Recommendations
- Monitor quantum computing developments
- Watch for AI regulation updates
- Track institutional crypto adoption`,
  
  2: `# Weekly Tech Roundup
## February 14, 2026

### Major Headlines
- Meta announces AR glasses for consumers
- OpenAI releases GPT-5 preview
- Tesla FSD reaches Level 4 autonomy

### Trending Topics
1. **Augmented Reality** (15 articles)
2. **Autonomous Vehicles** (12 articles)
3. **Space Technology** (8 articles)

### Deep Dive: AR Revolution
Apple and Meta are in a fierce battle for AR dominance...

### Investment Spotlight
- AR/VR startups raised $2.1B this week
- EV companies see mixed results
- Space sector attracts institutional money

### Global Tech Policy
- EU finalizes AI Act implementation
- US considers TikTok restrictions
- China expands semiconductor investments`,

  3: `# Market Analysis Summary
## February 13, 2026

### Executive Summary
Markets showed mixed signals as tech earnings season begins...

### Sector Performance
- **Technology**: +1.8%
- **Healthcare**: -0.5%
- **Energy**: +2.1%
- **Finance**: +0.3%

### Key Movers
- NVDA: +5.2% on AI chip demand
- TSLA: -3.1% on production concerns
- MSFT: +2.8% on cloud growth

### Analyst Notes
"The AI revolution continues to drive valuations in the tech sector, 
but concerns about sustainability are growing..."

### Risk Assessment
- Inflation concerns persist
- Geopolitical tensions in Asia
- Supply chain disruptions possible

### Outlook
Cautiously optimistic for Q1 2026, with AI and clean energy 
leading growth sectors.`
};

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [reportContent, setReportContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [contentLoading, setContentLoading] = useState(false);

  useEffect(() => {
    // 尝试从 API 获取报告，失败则使用 mock 数据
    fetchReports()
      .then(data => {
        setReports(data);
        if (data.length > 0) {
          setSelectedReport(data[0]);
        }
      })
      .catch(error => {
        console.log("API fetch failed, using mock data:", error.message);
        setReports(mockReports);
        setSelectedReport(mockReports[0]);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedReport) return;

    setContentLoading(true);
    // 尝试从 API 获取报告内容，失败则使用 mock 内容
    fetchReportContent(selectedReport.id)
      .then(content => {
        setReportContent(content);
      })
      .catch(error => {
        console.log("Content fetch failed, using mock content:", error.message);
        setReportContent(mockContent[selectedReport.id] || "Report content not available.");
      })
      .finally(() => setContentLoading(false));
  }, [selectedReport]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric"
    });
  };

  const formatMarkdown = (content: string) => {
    // 简单的 markdown 转换
    return content
      .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mb-4">$1</h1>')
      .replace(/^## (.*$)/gim, '<h2 class="text-xl font-semibold mb-3">$1</h2>')
      .replace(/^### (.*$)/gim, '<h3 class="text-lg font-medium mb-2">$1</h3>')
      .replace(/^\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
      .replace(/^\* (.*$)/gim, '<li class="ml-4">$1</li>')
      .replace(/^(\d+)\. (.*$)/gim, '<li class="ml-4">$2</li>')
      .replace(/\n/g, '<br />');
  };

  if (loading) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 pl-60">
          <Header title="Reports" />
          <div className="p-6">
            <div className="text-center">Loading reports...</div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 pl-60">
        <Header title="Reports" />
        <div className="flex h-[calc(100vh-3.5rem)]">
          {/* 左侧报告列表 */}
          <div className="w-1/3 border-r border-border">
            <ScrollArea className="h-full p-4">
              <div className="space-y-2">
                {reports.map((report) => (
                  <Card
                    key={report.id}
                    className={`cursor-pointer transition-colors hover:bg-accent ${
                      selectedReport?.id === report.id ? "border-primary bg-primary/5" : ""
                    }`}
                    onClick={() => setSelectedReport(report)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            <Badge variant="outline" className="text-xs">
                              {formatDate(report.date)}
                            </Badge>
                          </div>
                          <h3 className="font-medium text-sm leading-tight mb-2">
                            {report.title}
                          </h3>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <BarChart className="h-3 w-3" />
                              {report.article_count || 0} articles
                            </div>
                            <div className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {formatDate(report.created_at)}
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </div>

          {/* 右侧报告内容 */}
          <div className="flex-1">
            <ScrollArea className="h-full">
              {selectedReport ? (
                <div className="p-6">
                  <div className="mb-6">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="secondary">
                        {formatDate(selectedReport.date)}
                      </Badge>
                      <Badge variant="outline">
                        {selectedReport.article_count || 0} articles
                      </Badge>
                    </div>
                    <h1 className="text-2xl font-bold">{selectedReport.title}</h1>
                    <p className="text-sm text-muted-foreground mt-1">
                      Generated on {new Date(selectedReport.created_at).toLocaleString()}
                    </p>
                  </div>
                  <Separator className="mb-6" />
                  
                  {contentLoading ? (
                    <div className="text-center py-8">
                      <div className="text-muted-foreground">Loading content...</div>
                    </div>
                  ) : (
                    <div className="prose prose-sm max-w-none">
                      <div
                        className="space-y-4"
                        style={{ whiteSpace: "pre-wrap" }}
                        dangerouslySetInnerHTML={{
                          __html: formatMarkdown(reportContent)
                        }}
                      />
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-muted-foreground">
                    <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Select a report to view its content</p>
                  </div>
                </div>
              )}
            </ScrollArea>
          </div>
        </div>
      </main>
    </div>
  );
}