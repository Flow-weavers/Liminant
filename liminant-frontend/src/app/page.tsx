"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useStore } from "@/lib/store";
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

      <main className="flex-1 px-8 py-8">
        <h2 className="text-lg font-semibold mb-4">Sessions</h2>
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
          <div className="grid gap-4 max-w-3xl">
            {sessions.map((session) => (
              <Card key={session.id} className="group">
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex flex-col gap-1 min-w-0">
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
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
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
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
