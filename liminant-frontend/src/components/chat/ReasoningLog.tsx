"use client";

import { useStore } from "@/lib/store";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { Bot, Brain, BookOpen, Zap, CheckCircle, XCircle, Wrench, AlertCircle } from "lucide-react";

const PHASE_CONFIG: Record<string, { label: string; icon: typeof Bot; color: string }> = {
  absorbing: { label: "ABSORBING", icon: Brain, color: "text-blue-500" },
  constraining: { label: "CONSTRAINING", icon: BookOpen, color: "text-amber-500" },
  generating: { label: "GENERATING", icon: Zap, color: "text-purple-500" },
  validating: { label: "VALIDATING", icon: CheckCircle, color: "text-green-500" },
  done: { label: "DONE", icon: CheckCircle, color: "text-emerald-500" },
  idle: { label: "IDLE", icon: Bot, color: "text-gray-400" },
};

const STAGE_LABELS: Record<number, string> = {
  0: "Start",
  1: "Intent Analysis",
  2: "KB Retrieval",
  3: "Code/Text Generation",
  4: "Output Optimization",
};

export function ReasoningLog() {
  const { reasoningLog, clearReasoningLog } = useStore();

  if (reasoningLog.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-muted-foreground text-sm p-4 text-center">
        <Brain className="h-8 w-8 mb-2 opacity-20" />
        <p className="text-xs">Pipeline reasoning will appear here</p>
      </div>
    );
  }

  const lastEntry = reasoningLog[reasoningLog.length - 1];
  const latestStage = lastEntry?.pipeline_stage ?? 0;
  const isComplete = lastEntry?.pipeline_complete;

  const STAGE_ACTIVE_PHASE: Record<number, string> = {
    0: "idle",
    1: "constraining",
    2: "generating",
    3: "validating",
    4: "done",
  };
  const activePhaseKey = isComplete ? "done" : (STAGE_ACTIVE_PHASE[latestStage] ?? "idle");
  const phaseCfg = PHASE_CONFIG[activePhaseKey] || PHASE_CONFIG.idle;
  const PhaseIcon = phaseCfg.icon;

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <PhaseIcon className={cn("h-4 w-4", phaseCfg.color)} />
          <span className={cn("text-xs font-mono font-semibold", phaseCfg.color)}>
            {phaseCfg.label}
          </span>
        </div>
        <button
          onClick={clearReasoningLog}
          className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
        >
          Clear
        </button>
      </div>

      <ScrollArea className="flex-1 min-h-0">
        <div className="p-3 space-y-3">
          {reasoningLog.map((entry, idx) => (
            <div key={idx} className="rounded-lg border bg-card text-card-foreground shadow-sm overflow-hidden">
              <div className="px-3 py-2 bg-muted/50 border-b flex items-center gap-2">
                <Badge variant="outline" className="text-[10px] font-mono px-1.5 py-0.5">
                  #{idx + 1}
                </Badge>
                <span className="text-[10px] text-muted-foreground">
                  Stage {entry.pipeline_stage}: {STAGE_LABELS[entry.pipeline_stage] || "—"}
                </span>
                {entry.intent && (
                  <Badge variant="secondary" className="text-[10px] ml-auto">
                    {entry.intent}
                  </Badge>
                )}
              </div>

              <div className="px-3 py-2 space-y-2 text-xs">
                {entry.applied_constraints.length > 0 && (
                  <div>
                    <div className="flex items-center gap-1 text-muted-foreground mb-1">
                      <BookOpen className="h-3 w-3" />
                      <span className="text-[10px] uppercase tracking-wide">Constraints ({entry.applied_constraints.length})</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {entry.applied_constraints.map((c) => (
                        <Badge key={c.id} variant="secondary" className="text-[10px]">
                          {c.title || c.id}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {entry.kb_entries && entry.kb_entries.length > 0 && (
                  <div>
                    <div className="flex items-center gap-1 text-muted-foreground mb-1">
                      <Bot className="h-3 w-3" />
                      <span className="text-[10px] uppercase tracking-wide">KB Entries ({entry.kb_entries.length})</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {entry.kb_entries.slice(0, 5).map((e) => (
                        <Badge key={e.id} variant="outline" className="text-[10px]">
                          {e.title || e.id}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {entry.tools_used && entry.tools_used.length > 0 && (
                  <div>
                    <div className="flex items-center gap-1 text-muted-foreground mb-1">
                      <Wrench className="h-3 w-3" />
                      <span className="text-[10px] uppercase tracking-wide">Tools ({entry.tools_used.length})</span>
                    </div>
                    <div className="space-y-1">
                      {entry.tools_used.map((t, ti) => {
                        const success = t.result === true;
                        return (
                          <div key={ti} className="flex items-center gap-1.5 bg-muted/50 rounded px-2 py-1">
                            {success ? (
                              <CheckCircle className="h-3 w-3 text-emerald-500 shrink-0" />
                            ) : (
                              <XCircle className="h-3 w-3 text-red-500 shrink-0" />
                            )}
                            <span className="font-mono text-[10px]">{t.name}</span>
                            {t.args && Object.keys(t.args).length > 0 && (
                              <span className="text-[10px] text-muted-foreground truncate ml-1">
                                {JSON.stringify(t.args).slice(0, 40)}
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {!entry.applied_constraints.length && !entry.kb_entries?.length && !entry.tools_used?.length && (
                  <div className="flex items-center gap-1.5 text-muted-foreground">
                    <AlertCircle className="h-3 w-3" />
                    <span className="text-[10px]">No entries — check pipeline</span>
                  </div>
                )}

                {entry.pipeline_complete && (
                  <div className="flex items-center gap-1 text-emerald-500 pt-1">
                    <CheckCircle className="h-3 w-3" />
                    <span className="text-[10px]">Pipeline complete</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
