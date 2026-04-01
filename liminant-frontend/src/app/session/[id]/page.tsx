"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ChatPanel } from "@/components/chat";
import { ReasoningLog } from "@/components/chat/ReasoningLog";
import { PhaseIndicator } from "@/components/chat/PhaseIndicator";
import { useStore } from "@/lib/store";
import { ArrowLeft } from "lucide-react";

export default function SessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;
  const { activeSession, isLoading, setActiveSession, reasoningLog, connectStream, disconnectStream } = useStore();
  const lastEntry = reasoningLog[reasoningLog.length - 1];
  const currentPhase = lastEntry?.phase || "idle";

  useEffect(() => {
    if (sessionId) {
      setActiveSession(sessionId);
      connectStream(sessionId);
    }
    return () => {
      disconnectStream();
    };
  }, [sessionId, setActiveSession, connectStream, disconnectStream]);

  return (
    <div className="flex flex-col h-screen">
      <header className="border-b px-4 py-3 flex items-center gap-4 shrink-0">
        <Button variant="ghost" size="icon" onClick={() => router.push("/")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex flex-col">
          <span className="text-sm font-semibold">
            {activeSession ? `Session ${activeSession.id}` : "Loading..."}
          </span>
          {activeSession && (
            <span className="text-xs text-muted-foreground font-mono">
              {activeSession.context.working_directory}
            </span>
          )}
        </div>
        <div className="ml-auto flex items-center gap-3">
          <PhaseIndicator phase={currentPhase} />
        </div>
      </header>

      <div className="flex-1 overflow-hidden flex">
        <div className="flex-1 overflow-hidden">
          {isLoading && !activeSession ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              Loading session...
            </div>
          ) : (
            <ChatPanel />
          )}
        </div>

        <div className="w-80 border-l bg-muted/20 overflow-hidden flex flex-col shrink-0">
          <div className="px-3 py-2 border-b bg-background/50">
            <span className="text-xs font-semibold">Pipeline Trace</span>
          </div>
          <div className="flex-1 overflow-hidden">
            <ReasoningLog />
          </div>
        </div>
      </div>
    </div>
  );
}
