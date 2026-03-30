"use client";

import { useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Message } from "@/lib/api";

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
        <p className="text-lg font-medium">Liminal</p>
        <p className="text-sm">Start a conversation to cross the threshold</p>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 px-4">
      <div className="space-y-4 py-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex flex-col",
              msg.role === "user" ? "items-end" : "items-start"
            )}
          >
            <Badge
              variant={msg.role === "user" ? "default" : "secondary"}
              className="mb-1 text-xs"
            >
              {msg.role}
            </Badge>
            <div
              className={cn(
                "rounded-2xl px-4 py-2 max-w-[80%] text-sm whitespace-pre-wrap",
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              )}
            >
              {msg.content}
            </div>
            <span className="text-[10px] text-muted-foreground mt-1">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </span>
          </div>
        ))}
        {isLoading && (
          <div className="flex items-start">
            <Badge variant="secondary" className="mb-1 text-xs">assistant</Badge>
            <div className="rounded-2xl px-4 py-2 bg-muted text-sm">
              <span className="animate-pulse">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
