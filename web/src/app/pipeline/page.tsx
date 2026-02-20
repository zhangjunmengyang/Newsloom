"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Play, Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";
import {
  runPipeline,
  fetchPipelineStatus,
  fetchPipelineHistory,
  PipelineRun,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const statusConfig = {
  success: {
    icon: CheckCircle2,
    color: "text-green-500",
    bg: "bg-green-500/20",
    border: "border-green-500/30",
  },
  failed: {
    icon: XCircle,
    color: "text-red-500",
    bg: "bg-red-500/20",
    border: "border-red-500/30",
  },
  running: {
    icon: Loader2,
    color: "text-amber-500",
    bg: "bg-amber-500/20",
    border: "border-amber-500/30",
  },
  pending: {
    icon: Clock,
    color: "text-blue-500",
    bg: "bg-blue-500/20",
    border: "border-blue-500/30",
  },
};

export default function PipelinePage() {
  const [currentRun, setCurrentRun] = useState<PipelineRun | null>(null);
  const [history, setHistory] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const loadData = async () => {
    try {
      const [status, historyData] = await Promise.all([
        fetchPipelineStatus(),
        fetchPipelineHistory(10),
      ]);
      setCurrentRun(status);
      setHistory(historyData);
    } catch (error) {
      console.error("Failed to fetch pipeline data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Poll for updates if pipeline is running
    const interval = setInterval(() => {
      if (currentRun?.status === "running") {
        loadData();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [currentRun?.status]);

  const handleRunPipeline = async () => {
    try {
      setRunning(true);
      const newRun = await runPipeline();
      setCurrentRun(newRun);
      await loadData();
    } catch (error) {
      console.error("Failed to run pipeline:", error);
    } finally {
      setRunning(false);
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return "—";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const getStatusBadge = (status: string) => {
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    const Icon = config.icon;
    return (
      <Badge
        variant="outline"
        className={cn("text-xs", config.bg, config.color, config.border)}
      >
        <Icon className={cn("h-3 w-3 mr-1", status === "running" && "animate-spin")} />
        {status}
      </Badge>
    );
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 pl-60">
        <Header title="Pipeline Control" />
        <div className="p-6 space-y-6">
          {/* Pipeline Controls */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Pipeline Control</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Run and monitor the news processing pipeline
              </p>
            </div>
            <Button
              onClick={handleRunPipeline}
              disabled={running || currentRun?.status === "running"}
              className="bg-primary text-primary-foreground hover:bg-primary/90 gold-glow"
            >
              {running || currentRun?.status === "running" ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Run Pipeline
                </>
              )}
            </Button>
          </div>

          {/* Current Pipeline Status */}
          {currentRun && currentRun.status === "running" && (
            <Card className="border-primary/30">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Current Run</CardTitle>
                  {getStatusBadge(currentRun.status)}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-muted-foreground">
                      Current Layer: <span className="text-foreground font-medium">{currentRun.current_layer || "—"}</span>
                    </span>
                    <span className="text-primary font-medium">
                      {currentRun.progress_percent}%
                    </span>
                  </div>
                  <Progress value={currentRun.progress_percent} className="h-2" />
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Started</div>
                    <div className="font-medium">
                      {new Date(currentRun.started_at).toLocaleTimeString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Layers</div>
                    <div className="font-medium">{currentRun.layers.join(" → ")}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Pipeline Status Summary */}
          {!currentRun || currentRun.status !== "running" ? (
            <Card>
              <CardHeader>
                <CardTitle>Pipeline Status</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <p className="text-sm text-muted-foreground">Loading status...</p>
                ) : !currentRun ? (
                  <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                    <Play className="h-12 w-12 mb-3 opacity-50" />
                    <p className="text-sm">No pipeline runs yet</p>
                    <p className="text-xs mt-1">Click "Run Pipeline" to start</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Last Run Status</span>
                      {getStatusBadge(currentRun.status)}
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <div className="text-muted-foreground">Date</div>
                        <div className="font-medium">{currentRun.date}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Duration</div>
                        <div className="font-medium">
                          {formatDuration(currentRun.duration_seconds)}
                        </div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Layers</div>
                        <div className="font-medium">{currentRun.layers.length}</div>
                      </div>
                    </div>
                    {currentRun.error_message && (
                      <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                        <p className="text-sm text-red-400">{currentRun.error_message}</p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ) : null}

          {/* Run History */}
          <Card>
            <CardHeader>
              <CardTitle>Run History</CardTitle>
            </CardHeader>
            <CardContent>
              {history.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No pipeline runs in history
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Layers</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Started</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {history.map((run) => (
                      <TableRow key={run.id}>
                        <TableCell className="font-medium">{run.date}</TableCell>
                        <TableCell>{getStatusBadge(run.status)}</TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {run.layers.join(", ")}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {formatDuration(run.duration_seconds)}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {new Date(run.started_at).toLocaleString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
