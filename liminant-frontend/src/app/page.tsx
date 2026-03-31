"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useStore } from "@/lib/store";
import { DashboardStats } from "@/components/dashboard/DashboardStats";
import { QuickAddKB } from "@/components/knowledge/QuickAddKB";
import { Plus, Trash2, ArrowRight } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const { sessions, loadSessions, createSession, deleteSession, setActiveSession } = useStore();

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleNew = async () => {
    const id = await createSession();
    setActiveSession(id);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="border-b px-8 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Liminal</h1>
          <p className="text-sm text-muted-foreground">Vibe Engineering Platform</p>
        </div>
        <Button onClick={handleNew}>
          <Plus className="mr-2 h-4 w-4" />
          New Session
        </Button>
      </header>

      <main className="flex-1 px-8 py-8 max-w-5xl mx-auto w-full">
        <DashboardStats />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Sessions</h2>
            </div>

            {sessions.length === 0 ? (
              <Card className="max-w-md mx-auto">
                <CardHeader>
                  <CardTitle className="text-center">Cross the threshold</CardTitle>
                </CardHeader>
                <CardContent className="text-center text-muted-foreground text-sm">
                  No sessions yet. Create one to start building.
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {sessions.map((session) => (
                  <Card key={session.id} className="group">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div className="flex flex-col gap-1 min-w-0 flex-1 cursor-pointer" onClick={() => { setActiveSession(session.id); router.push(`/session/${session.id}`); }}>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {session.state.phase}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {new Date(session.updated_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm truncate">
                          {session.messages.length > 0
                            ? session.messages[session.messages.length - 1].content.slice(0, 80)
                            : "Empty session"}
                        </p>
                        <p className="text-xs text-muted-foreground font-mono">
                          {session.context.working_directory}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity ml-4">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveSession(session.id);
                            router.push(`/session/${session.id}`);
                          }}
                        >
                          <ArrowRight className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteSession(session.id);
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-4">
            <QuickAddKB onAdded={loadSessions} />
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
              <div className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">Session Tips</div>
              <div className="space-y-2 text-xs text-zinc-500">
                <p>• Type <code className="text-zinc-300">.list changes</code> to see recent activity</p>
                <p>• Type <code className="text-zinc-300">.summarize</code> to condense session context</p>
                <p>• Add rules in the Knowledge Base to enforce coding standards</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
