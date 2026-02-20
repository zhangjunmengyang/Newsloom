"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  FileText,
  Database,
  Play,
  Settings,
  Newspaper,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navSections = [
  {
    label: "OVERVIEW",
    items: [
      { href: "/", label: "Dashboard", icon: LayoutDashboard },
      { href: "/reports", label: "Reports", icon: FileText },
    ],
  },
  {
    label: "CONTENT",
    items: [
      { href: "/sources", label: "Data Sources", icon: Database },
      { href: "/pipeline", label: "Pipeline", icon: Play },
    ],
  },
  {
    label: "SYSTEM",
    items: [{ href: "/settings", label: "Settings", icon: Settings }],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [apiStatus, setApiStatus] = useState<"online" | "offline">("offline");

  useEffect(() => {
    // Check API status
    fetch("http://localhost:8080/api/v1/dashboard/stats")
      .then(() => setApiStatus("online"))
      .catch(() => setApiStatus("offline"));
  }, []);

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-60 border-r border-border bg-card flex flex-col">
      <div className="flex h-14 items-center gap-2 border-b border-border px-4">
        <Newspaper className="h-6 w-6 text-primary" />
        <span className="text-lg font-bold">Newsloom</span>
      </div>

      <nav className="flex-1 space-y-6 p-3 overflow-y-auto">
        {navSections.map((section) => (
          <div key={section.label}>
            <div className="text-xs font-semibold text-muted-foreground mb-2 px-3">
              {section.label}
            </div>
            <div className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors relative",
                      isActive
                        ? "text-primary font-medium border-l-2 border-primary"
                        : "text-muted-foreground hover:bg-accent hover:text-foreground border-l-2 border-transparent"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* API Status Indicator */}
      <div className="border-t border-border p-4">
        <div className="flex items-center gap-2 text-xs">
          <div
            className={cn(
              "h-2 w-2 rounded-full",
              apiStatus === "online"
                ? "animate-pulse"
                : ""
            )}
            style={{
              backgroundColor: apiStatus === "online"
                ? "hsl(var(--chart-3))"
                : "hsl(var(--destructive))"
            }}
          />
          <span className="text-muted-foreground">
            API {apiStatus === "online" ? "Online" : "Offline"}
          </span>
        </div>
      </div>
    </aside>
  );
}