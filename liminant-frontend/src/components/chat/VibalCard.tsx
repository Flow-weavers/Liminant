"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp } from "lucide-react";

const QUICK_COMMANDS = [
  { label: ".list changes", description: "Show recent session changes" },
  { label: ".summarize", description: "Summarize current session" },
  { label: ".explain", description: "Explain recent decisions" },
  { label: ".diff", description: "Show changes since last turn" },
];

interface VibalCardProps {
  onSend: (content: string) => void;
  disabled?: boolean;
}

export function VibalCard({ onSend, disabled }: VibalCardProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="border-t bg-muted/30">
      <button
        onClick={() => setCollapsed((c) => !c)}
        className="w-full px-4 py-1.5 flex items-center justify-between text-[10px] text-muted-foreground hover:text-foreground transition-colors"
        disabled={disabled}
      >
        <span className="font-mono tracking-wider">VIBAL COMMANDS</span>
        {collapsed ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronUp className="h-3 w-3" />
        )}
      </button>

      {!collapsed && (
        <div className="px-4 pb-3">
          <div className="bg-muted border rounded-lg p-2 font-mono text-xs">
            <div className="space-y-1">
              {QUICK_COMMANDS.map((cmd) => (
                <button
                  key={cmd.label}
                  onClick={() => !disabled && onSend(cmd.label)}
                  disabled={disabled}
                  className={cn(
                    "w-full flex items-start gap-2 rounded px-2 py-1 text-left transition-colors hover:bg-black/5 dark:hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed",
                    disabled && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <span className="text-muted-foreground shrink-0 mt-0.5">›</span>
                  <span className="text-foreground">{cmd.label}</span>
                  <span className="text-muted-foreground/60">— {cmd.description}</span>
                </button>
              ))}
            </div>
            <div className="mt-2 pt-2 border-t border-border/50 text-[10px] text-muted-foreground/60">
              Commands parsed dynamically by LLM — no fixed syntax required
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
