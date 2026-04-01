"use client";

import { useStore } from "@/lib/store";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { Sparkles, Brain, BookOpen, Paperclip, Send, X, Loader2, Zap } from "lucide-react";

const INTENT_COLORS: Record<string, string> = {
  file_creation: "bg-blue-500/10 text-blue-600 border-blue-500/30",
  modification: "bg-amber-500/10 text-amber-600 border-amber-500/30",
  deletion: "bg-red-500/10 text-red-600 border-red-500/30",
  explanation: "bg-purple-500/10 text-purple-600 border-purple-500/30",
  summarization: "bg-green-500/10 text-green-600 border-green-500/30",
  search: "bg-cyan-500/10 text-cyan-600 border-cyan-500/30",
  execution: "bg-orange-500/10 text-orange-600 border-orange-500/30",
  vibal_command: "bg-pink-500/10 text-pink-600 border-pink-500/30",
  request: "bg-violet-500/10 text-violet-600 border-violet-500/30",
  general: "bg-gray-500/10 text-gray-600 border-gray-500/30",
};

export function PreFlightCard() {
  const { preflight, runPreflight, confirmPreflight, dismissPreflight } = useStore();

  if (!preflight.visible) return null;

  return (
    <div className="border-b bg-gradient-to-r from-blue-50/50 to-purple-50/50 dark:from-blue-950/30 dark:to-purple-950/30">
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-blue-500" />
            <span className="text-xs font-semibold text-foreground">Pre-flight Check</span>
          </div>
          <button
            onClick={dismissPreflight}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mb-3">
          <div className="flex items-center gap-2 mb-2">
            <Badge
              variant="outline"
              className={cn("text-xs", INTENT_COLORS[preflight.intent] || INTENT_COLORS.general)}
            >
              <Zap className="h-3 w-3 mr-1" />
              {preflight.intent_label}
            </Badge>
            {preflight.loading ? (
              <Badge variant="outline" className="text-xs bg-muted">
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                Analyzing...
              </Badge>
            ) : (
              <div className="flex items-center gap-1">
                <span className="text-[10px] text-muted-foreground">Confidence</span>
                <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                    style={{ width: `${preflight.confidence * 100}%` }}
                  />
                </div>
                <span className="text-[10px] text-muted-foreground">{Math.round(preflight.confidence * 100)}%</span>
              </div>
            )}
          </div>

          <p className="text-xs text-muted-foreground bg-muted/50 rounded px-2 py-1.5 font-mono truncate">
            {preflight.user_input}
          </p>
        </div>

        {preflight.loading ? null : (
          <>
            {preflight.requirements.length > 0 && (
              <div className="mb-3">
                <div className="flex items-center gap-1 mb-1.5">
                  <Brain className="h-3 w-3 text-muted-foreground" />
                  <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                    Requirements
                  </span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {preflight.requirements.map((req, i) => (
                    <Badge key={i} variant="secondary" className="text-[10px] px-1.5 py-0.5">
                      {req}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {preflight.kb_entries.length > 0 && (
              <div className="mb-3">
                <div className="flex items-center gap-1 mb-1.5">
                  <BookOpen className="h-3 w-3 text-muted-foreground" />
                  <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                    Active Constraints ({preflight.kb_entries.length})
                  </span>
                </div>
                <ScrollArea className="max-h-28">
                  <div className="space-y-1 pr-2">
                    {preflight.kb_entries.map((entry) => (
                      <div
                        key={entry.id}
                        className="flex items-start gap-2 rounded border bg-card/60 p-1.5 text-[10px]"
                      >
                        <Badge variant="outline" className="shrink-0 mt-0.5">
                          {entry.type}
                        </Badge>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-foreground truncate">{entry.title}</p>
                          {entry.content_preview && (
                            <p className="text-muted-foreground line-clamp-2 mt-0.5">
                              {entry.content_preview}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            )}

            {preflight.anchors.length > 0 && (
              <div className="mb-3">
                <div className="flex items-center gap-1 mb-1.5">
                  <Paperclip className="h-3 w-3 text-muted-foreground" />
                  <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                    Context Anchors
                  </span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {preflight.anchors.map((anchor) => (
                    <Badge key={anchor.id} variant="secondary" className="text-[10px]">
                      {anchor.type}: {anchor.label}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        <div className="flex items-center justify-end gap-2 mt-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={dismissPreflight}
            className="h-7 text-xs"
          >
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={confirmPreflight}
            disabled={preflight.loading}
            className="h-7 text-xs gap-1.5"
          >
            {preflight.loading ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Send className="h-3 w-3" />
            )}
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
