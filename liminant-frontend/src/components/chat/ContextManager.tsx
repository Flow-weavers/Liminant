"use client";

import { useStore } from "@/lib/store";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { Layers, File, MessageSquare } from "lucide-react";

export function ContextManager() {
  const { preflight, toggleContextAnchor } = useStore();

  if (!preflight.visible || preflight.loading) return null;
  if (preflight.anchors.length === 0) return null;

  const enabledCount = preflight.context_enabled.length;
  const totalCount = preflight.anchors.length;
  const allEnabled = enabledCount === totalCount;

  return (
    <div className="border-t bg-muted/20">
      <div className="px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Layers className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
            Context ({enabledCount}/{totalCount})
          </span>
        </div>
        <button
          onClick={() => {
            if (allEnabled) {
              preflight.anchors.forEach((a) => {
                if (preflight.context_enabled.includes(a.id)) {
                  toggleContextAnchor(a.id);
                }
              });
            } else {
              preflight.anchors.forEach((a) => {
                if (!preflight.context_enabled.includes(a.id)) {
                  toggleContextAnchor(a.id);
                }
              });
            }
          }}
          className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
        >
          {allEnabled ? "Disable all" : "Enable all"}
        </button>
      </div>

      <ScrollArea className="max-h-36">
        <div className="px-4 pb-3 space-y-1">
          {preflight.anchors.map((anchor) => {
            const isEnabled = preflight.context_enabled.includes(anchor.id);
            return (
              <button
                key={anchor.id}
                onClick={() => toggleContextAnchor(anchor.id)}
                className={cn(
                  "w-full flex items-center gap-2 rounded-lg px-2 py-1.5 text-left transition-all text-xs",
                  isEnabled
                    ? "bg-background/80 border border-border/50"
                    : "bg-muted/50 opacity-50"
                )}
              >
                <div
                  className={cn(
                    "w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-colors",
                    isEnabled ? "bg-primary border-primary" : "border-muted-foreground/30"
                  )}
                >
                  {isEnabled && (
                    <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
                      <path d="M1 4L3 6L7 2" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </div>
                {anchor.type === "artifact" || anchor.type === "file" ? (
                  <File className="h-3 w-3 text-muted-foreground shrink-0" />
                ) : (
                  <MessageSquare className="h-3 w-3 text-muted-foreground shrink-0" />
                )}
                <span className="truncate text-foreground/80">{anchor.label}</span>
              </button>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
