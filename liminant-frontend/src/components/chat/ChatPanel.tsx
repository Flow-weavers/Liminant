"use client";

import { Card } from "@/components/ui/card";
import { MessageList } from "./MessageList";
import { InputArea } from "./InputArea";
import { useStore } from "@/lib/store";

export function ChatPanel() {
  const { messages, isLoading } = useStore();

  return (
    <Card className="flex flex-col h-full border-0 rounded-none">
      <MessageList messages={messages} isLoading={isLoading} />
      <div className="p-4 border-t">
        <InputArea />
      </div>
    </Card>
  );
}
