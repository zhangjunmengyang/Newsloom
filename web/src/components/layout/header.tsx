"use client";

import { RefreshCw, Palette } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";
import { useTheme } from "@/lib/theme";

export function Header({ title }: { title: string }) {
  const [time, setTime] = useState("");
  const { theme, setTheme, themes } = useTheme();

  useEffect(() => {
    const update = () =>
      setTime(new Date().toLocaleTimeString("en-US", { hour12: false }));
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  const cycleTheme = () => {
    const currentIndex = themes.findIndex(t => t.id === theme);
    const nextIndex = (currentIndex + 1) % themes.length;
    setTheme(themes[nextIndex].id);
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b bg-background/80 px-6 backdrop-blur relative">
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
      <h1 className="text-lg font-semibold">{title}</h1>
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground font-mono">{time}</span>
        <Button
          variant="ghost"
          size="icon"
          onClick={cycleTheme}
          title={`Current: ${themes.find(t => t.id === theme)?.name} - Click to cycle`}
        >
          <Palette className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" onClick={() => window.location.reload()}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}