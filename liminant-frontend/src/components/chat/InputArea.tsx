"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Loader2 } from "lucide-react";

interface InputAreaProps {
  onSend?: (content: string) => void;
  onAnalyze?: (content: string) => void;
  isLoading?: boolean;
}

export function InputArea({ onSend, onAnalyze, isLoading }: InputAreaProps) {
  const [input, setInput] = useState("");

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    if (onAnalyze) {
      onAnalyze(trimmed);
    } else if (onSend) {
      onSend(trimmed);
    }
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t p-4 bg-background/95 backdrop-blur">
      <div className="flex gap-2 items-end max-w-4xl mx-auto">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe what you want to build or change..."
          className="min-h-[44px] max-h-[200px] resize-none rounded-2xl"
          disabled={isLoading}
          rows={1}
        />
        <Button
          onClick={handleSubmit}
          disabled={!input.trim() || isLoading}
          size="icon"
          className="rounded-2xl h-[44px] w-[44px] shrink-0"
        >
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}
