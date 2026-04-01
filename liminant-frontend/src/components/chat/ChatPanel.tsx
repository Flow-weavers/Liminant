"use client";

import { Card } from "@/components/ui/card";
import { MessageList } from "./MessageList";
import { InputArea } from "./InputArea";
import { PreFlightCard } from "./PreFlightCard";
import { useStore } from "@/lib/store";

export function ChatPanel() {
  const { messages, isLoading, runPreflight } = useStore();

  return (
    <Card className="flex flex-col h-full border-0 rounded-none">
      <PreFlightCard />
      <MessageList messages={messages} isLoading={isLoading} />
      <InputArea onAnalyze={runPreflight} isLoading={isLoading} />
    </Card>
  );
}
