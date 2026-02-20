"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { RefreshCw, Database } from "lucide-react";
import { fetchSources, syncSourcesFromConfig, toggleSource, Source } from "@/lib/api";
import { cn } from "@/lib/utils";

const sourceTypeColors: Record<string, string> = {
  rss: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  arxiv: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  github: "bg-green-500/20 text-green-400 border-green-500/30",
  hackernews: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  reddit: "bg-red-500/20 text-red-400 border-red-500/30",
  crypto_market: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  producthunt: "bg-pink-500/20 text-pink-400 border-pink-500/30",
};

const channelColors: Record<string, string> = {
  ai: "bg-violet-500/20 text-violet-400 border-violet-500/30",
  tech: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  crypto: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  finance: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  community: "bg-rose-500/20 text-rose-400 border-rose-500/30",
  papers: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
  github: "bg-teal-500/20 text-teal-400 border-teal-500/30",
};

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const loadSources = async () => {
    try {
      setLoading(true);
      const data = await fetchSources();
      setSources(data);
    } catch (error) {
      console.error("Failed to fetch sources:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSources();
  }, []);

  const handleSync = async () => {
    try {
      setSyncing(true);
      await syncSourcesFromConfig();
      await loadSources();
    } catch (error) {
      console.error("Failed to sync sources:", error);
    } finally {
      setSyncing(false);
    }
  };

  const handleToggle = async (id: number) => {
    try {
      await toggleSource(id);
      setSources(sources.map(s => s.id === id ? { ...s, enabled: !s.enabled } : s));
    } catch (error) {
      console.error("Failed to toggle source:", error);
    }
  };

  const getFeedCount = (source: Source): number | null => {
    if (source.source_type === 'rss' && source.config?.feeds) {
      return Array.isArray(source.config.feeds) ? source.config.feeds.length : 0;
    }
    return null;
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 pl-60">
        <Header title="Data Sources" />
        <div className="p-6 space-y-6">
          {/* Header Actions */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Data Sources</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Manage your news sources and content feeds
              </p>
            </div>
            <Button
              onClick={handleSync}
              disabled={syncing}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              <RefreshCw className={cn("h-4 w-4 mr-2", syncing && "animate-spin")} />
              Sync from Config
            </Button>
          </div>

          {/* Sources Grid */}
          {loading ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading sources...</p>
            </div>
          ) : sources.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Database className="h-16 w-16 text-muted-foreground mb-4 opacity-50" />
                <h3 className="text-xl font-semibold mb-2">No sources found</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Click "Sync from Config" to import sources from your configuration
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {sources.map((source) => {
                const feedCount = getFeedCount(source);
                return (
                  <Card key={source.id} className="card-hover">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <CardTitle className="text-base truncate">
                            {source.name}
                          </CardTitle>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge
                              variant="outline"
                              className={cn(
                                "text-xs",
                                sourceTypeColors[source.source_type] ||
                                  "bg-gray-500/20 text-gray-400"
                              )}
                            >
                              {source.source_type}
                            </Badge>
                            <Badge
                              variant="outline"
                              className={cn(
                                "text-xs",
                                channelColors[source.channel] ||
                                  "bg-gray-500/20 text-gray-400"
                              )}
                            >
                              {source.channel}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between">
                        <div className="text-sm text-muted-foreground">
                          {feedCount !== null && (
                            <span>{feedCount} feed{feedCount !== 1 ? 's' : ''}</span>
                          )}
                          {feedCount === null && (
                            <span className="text-xs">
                              Added {new Date(source.created_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">
                            {source.enabled ? "Enabled" : "Disabled"}
                          </span>
                          <Switch
                            checked={source.enabled}
                            onCheckedChange={() => handleToggle(source.id)}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {/* Stats Summary */}
          {sources.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-primary">
                      {sources.length}
                    </div>
                    <div className="text-xs text-muted-foreground">Total Sources</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-500">
                      {sources.filter(s => s.enabled).length}
                    </div>
                    <div className="text-xs text-muted-foreground">Enabled</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-muted-foreground">
                      {sources.filter(s => !s.enabled).length}
                    </div>
                    <div className="text-xs text-muted-foreground">Disabled</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
