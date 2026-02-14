import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 pl-60">
        <Header title="Settings" />
        <div className="p-6">
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <Settings className="h-16 w-16 text-muted-foreground mb-4" />
              <h2 className="text-xl font-semibold mb-2">Settings</h2>
              <p className="text-muted-foreground text-center">
                Coming Soon
              </p>
              <p className="text-sm text-muted-foreground text-center mt-2">
                Configure your Newsloom settings and preferences here.
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}