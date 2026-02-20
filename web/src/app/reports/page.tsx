"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { FileText, Calendar, BarChart, Download, FileCode } from "lucide-react";
import { fetchReports, fetchReportContent, Report } from "@/lib/api";

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [reportContent, setReportContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [contentLoading, setContentLoading] = useState(false);

  useEffect(() => {
    const loadReports = async () => {
      try {
        const data = await fetchReports();
        setReports(data);
        if (data.length > 0) {
          setSelectedReport(data[0]);
        }
      } catch (error) {
        console.error("Failed to fetch reports:", error);
      } finally {
        setLoading(false);
      }
    };
    loadReports();
  }, []);

  useEffect(() => {
    if (!selectedReport) return;

    const loadContent = async () => {
      try {
        setContentLoading(true);
        const content = await fetchReportContent(selectedReport.id);
        setReportContent(content);
      } catch (error) {
        console.error("Failed to fetch report content:", error);
        setReportContent("Failed to load report content.");
      } finally {
        setContentLoading(false);
      }
    };
    loadContent();
  }, [selectedReport]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric"
    });
  };

  const handleDownload = (type: "pdf" | "html") => {
    if (!selectedReport) return;

    const path = type === "pdf" ? selectedReport.pdf_path : selectedReport.html_path;
    if (!path) {
      alert(`${type.toUpperCase()} file not available for this report`);
      return;
    }

    // Download the file
    window.open(`http://localhost:8080${path}`, "_blank");
  };

  const formatMarkdown = (content: string) => {
    // Simple markdown conversion
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
          {/* Left: Reports List */}
          <div className="w-1/3 border-r border-border">
            <ScrollArea className="h-full p-4">
              {reports.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                  <FileText className="h-16 w-16 mb-4 opacity-50" />
                  <p className="text-sm">No reports found</p>
                  <p className="text-xs mt-1">Run the pipeline to generate reports</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {reports.map((report) => (
                    <Card
                      key={report.id}
                      className={`cursor-pointer card-hover ${
                        selectedReport?.id === report.id ? "border-primary bg-primary/5" : ""
                      }`}
                      onClick={() => setSelectedReport(report)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <FileText className="h-4 w-4 text-primary" />
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
              )}
            </ScrollArea>
          </div>

          {/* Right: Report Content */}
          <div className="flex-1">
            <ScrollArea className="h-full">
              {selectedReport ? (
                <div className="p-6">
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">
                          {formatDate(selectedReport.date)}
                        </Badge>
                        <Badge variant="outline">
                          {selectedReport.article_count || 0} articles
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        {selectedReport.pdf_path && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDownload("pdf")}
                            className="hover:border-primary/50"
                          >
                            <Download className="h-3 w-3 mr-1" />
                            PDF
                          </Button>
                        )}
                        {selectedReport.html_path && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDownload("html")}
                            className="hover:border-primary/50"
                          >
                            <FileCode className="h-3 w-3 mr-1" />
                            HTML
                          </Button>
                        )}
                      </div>
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
                    <div className="prose prose-sm max-w-none dark:prose-invert">
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