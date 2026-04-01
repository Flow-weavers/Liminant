"use client";

import { Card } from "@/components/ui/card";
import { MessageList } from "./MessageList";
import { InputArea } from "./InputArea";
import { PreFlightCard } from "./PreFlightCard";
import { ContextManager } from "./ContextManager";
import { VibalCard } from "./VibalCard";
import { useStore } from "@/lib/store";

export function ChatPanel() {
  const { messages, isLoading, runPreflight, sendMessage } = useStore();

  return (
    <Card className="flex flex-col h-full border-0 rounded-none">
      <PreFlightCard />
      <ContextManager />
      <MessageList messages={messages} isLoading={isLoading} />
      <VibalCard onSend={sendMessage} disabled={isLoading} />
      <InputArea onAnalyze={runPreflight} isLoading={isLoading} />
    </Card>
  );
}
