"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ChatPanel } from "@/components/chat";
import { SessionTimeline } from "@/components/timeline/SessionTimeline";
import { ArtifactsPanel } from "@/components/artifacts/ArtifactsPanel";
import { useStore } from "@/lib/store";
import { ArrowLeft, Clock, MessageSquare, FileCode } from "lucide-react";

export default function SessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;
  const { activeSession, isLoading, setActiveSession } = useStore();
  const [activeTab, setActiveTab] = useState<"chat" | "timeline" | "artifacts">("chat");

  useEffect(() => {
    if (sessionId) {
      setActiveSession(sessionId);
    }
  }, [sessionId, setActiveSession]);

  return (
    <div className="flex flex-col h-screen">
      <header className="border-b px-4 py-3 flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push("/")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex flex-col flex-1">
          <span className="text-sm font-semibold">
            {activeSession ? `Session ${activeSession.id}` : "Loading..."}
          </span>
          {activeSession && (
            <span className="text-xs text-muted-foreground font-mono">
              {activeSession.context.working_directory}
            </span>
          )}
        </div>
        <div className="flex gap-1 bg-zinc-900 rounded-lg p-1">
          {(["chat", "timeline", "artifacts"] as const).map((tab) => {
            const icons = { chat: MessageSquare, timeline: Clock, artifacts: FileCode };
            const Icon = icons[tab];
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-colors ${
                  activeTab === tab
                    ? "bg-zinc-800 text-zinc-100"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                <Icon className="h-3 w-3" />
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            );
          })}
        </div>
      </header>

      <div className="flex-1 overflow-hidden">
        {isLoading && !activeSession ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            Loading session...
          </div>
        ) : activeTab === "chat" ? (
          <ChatPanel />
        ) : activeTab === "timeline" ? (
          <div className="h-full overflow-y-auto p-4">
            <SessionTimeline sessionId={sessionId} />
          </div>
        ) : (
          <div className="h-full overflow-hidden flex flex-col">
            <ArtifactsPanel sessionId={sessionId} />
          </div>
        )}
      </div>
    </div>
  );
}
