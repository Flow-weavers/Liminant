"use client";

import { useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { CodeBlock } from "./CodeBlock";
import { Message } from "@/lib/api";

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

type Part =
  | { kind: "text"; content: string }
  | { kind: "code"; content: string; lang: string }
  | { kind: "diff"; content: string; lang: string };

function parseContent(content: string): Part[] {
  const parts: Part[] = [];
  const codeBlockRe = /```(\w*)\n?([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = codeBlockRe.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ kind: "text", content: content.slice(lastIndex, match.index) });
    }
    const lang = match[1] || "text";
    const body = match[2].trim();
    const isDiff = lang === "diff" || body.includes("+++") || body.includes("---");
    parts.push({ kind: isDiff ? "diff" : "code", content: body, lang });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < content.length) {
    parts.push({ kind: "text", content: content.slice(lastIndex) });
  }

  return parts.length > 0 ? parts : [{ kind: "text", content }];
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
              {msg.role === "user" ? (
                msg.content
              ) : (
                <div className="space-y-2">
                  {parseContent(msg.content).map((part, i) => {
                    if (part.kind === "text") {
                      return <span key={i}>{part.content}</span>;
                    }
                    if (part.kind === "diff") {
                      return <CodeBlock key={i} code={part.content} language={part.lang} showDiff />;
                    }
                    return <CodeBlock key={i} code={part.content} language={part.lang} />;
                  })}
                </div>
              )}
            </div>
            <span className="text-[10px] text-muted-foreground mt-1">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </span>
          </div>
        ))}
        {isLoading && (
          <div className="flex items-start">
            <Badge variant="secondary" className="mb-1 text-xs">assistant</Badge>
            <div className="bg-muted rounded-2xl px-4 py-2">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:0.15s]" />
                <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:0.3s]" />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
