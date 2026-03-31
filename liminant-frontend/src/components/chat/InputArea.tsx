"use client";
import { useState, useCallback } from "react";
import { useStore } from "@/lib/store";

interface VibeSuggestion {
  intent: string;
  confidence: number;
  is_vibal_command: boolean;
  modifiers: Record<string, unknown>;
  suggested_actions: string[];
}

export function InputArea() {
  const { sendMessage, isLoading, activeSessionId } = useStore();
  const [input, setInput] = useState("");
  const [suggestion, setSuggestion] = useState<VibeSuggestion | null>(null);
  const [showVibe, setShowVibe] = useState(false);

  const analyze = useCallback(async (text: string) => {
    if (!text.trim()) { setSuggestion(null); return; }
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/vibesense/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      setSuggestion({
        intent: data.intent,
        confidence: data.confidence,
        is_vibal_command: data.is_vibal_command,
        modifiers: data.modifiers || {},
        suggested_actions: data.suggested_actions || [],
      });
    } catch { setSuggestion(null); }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setInput(val);
    if (val.length > 3) analyze(val);
    else setSuggestion(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !activeSessionId) return;
    const text = input.trim();
    setInput("");
    setSuggestion(null);
    setShowVibe(false);
    await sendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="space-y-2">
      {suggestion && showVibe && (
        <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-3 text-xs">
          <div className="flex items-center justify-between mb-1">
            <span className="font-semibold text-zinc-400">VibeSense</span>
            <span className="text-zinc-600">{Math.round(suggestion.confidence * 100)}%</span>
          </div>
          <div className="flex gap-2 flex-wrap">
            <span className="bg-blue-900 text-blue-300 px-1.5 py-0.5 rounded text-[10px]">
              {suggestion.intent}
            </span>
            {suggestion.is_vibal_command && (
              <span className="bg-green-900 text-green-300 px-1.5 py-0.5 rounded text-[10px]">vibal</span>
            )}
          </div>
          {suggestion.suggested_actions.length > 0 && (
            <div className="mt-1.5 text-zinc-500">
              → {suggestion.suggested_actions[0]}
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} className="relative">
        <textarea
          value={input}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setShowVibe(true)}
          placeholder="Send a message or try .list changes --detailed[~4]..."
          disabled={isLoading || !activeSessionId}
          rows={3}
          className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 resize-none focus:outline-none focus:border-zinc-500 disabled:opacity-50"
        />
        <div className="flex items-center justify-between mt-1.5">
          <button
            type="button"
            onClick={() => setShowVibe((v) => !v)}
            className="text-[10px] text-zinc-600 hover:text-zinc-400 transition-colors"
          >
            {showVibe ? "hide vibe" : "show vibe"}
          </button>
          <button
            type="submit"
            disabled={!input.trim() || isLoading || !activeSessionId}
            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-sm px-4 py-1.5 rounded-lg transition-colors"
          >
            {isLoading ? "Sending..." : "Send"}
          </button>
        </div>
      </form>
    </div>
  );
}
