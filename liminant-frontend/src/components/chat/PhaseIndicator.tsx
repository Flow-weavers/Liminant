"use client";

import { cn } from "@/lib/utils";

const PHASES = [
  { key: "absorbing", label: "ABSORBING", icon: "◎" },
  { key: "constraining", label: "CONSTRAINING", icon: "◉" },
  { key: "generating", label: "GENERATING", icon: "◈" },
  { key: "validating", label: "VALIDATING", icon: "◇" },
  { key: "done", label: "DONE", icon: "●" },
] as const;

const PHASE_ORDER = PHASES.map((p) => p.key);

function getPhaseIndex(phase: string): number {
  const idx = PHASE_ORDER.indexOf(phase.toLowerCase() as typeof PHASE_ORDER[number]);
  if (idx === -1) return PHASES.length - 1;
  return idx;
}

interface PhaseIndicatorProps {
  phase: string;
  className?: string;
}

export function PhaseIndicator({ phase, className }: PhaseIndicatorProps) {
  const current = phase.toLowerCase();
  const currentIdx = getPhaseIndex(current);

  return (
    <div className={cn("flex items-center gap-1", className)}>
      {PHASES.map((p, i) => {
        const isActive = i === currentIdx + 1;
        const isPast = i <= currentIdx;
        const isLast = i === PHASES.length - 1;

        return (
          <div key={p.key} className="flex items-center gap-1">
            <div className="flex flex-col items-center gap-0.5">
              <div
                className={cn(
                  "flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-mono transition-all duration-300",
                  isActive && "bg-primary text-primary-foreground scale-110 shadow-sm",
                  isPast && "bg-primary/60 text-primary-foreground",
                  !isActive && !isPast && "bg-muted text-muted-foreground"
                )}
              >
                {p.icon}
              </div>
              <span
                className={cn(
                  "text-[9px] font-mono tracking-wider transition-colors duration-200",
                  isActive && "text-primary font-semibold",
                  isPast && "text-primary/70",
                  !isActive && !isPast && "text-muted-foreground"
                )}
              >
                {p.label}
              </span>
            </div>
            {!isLast && (
              <div
                className={cn(
                  "h-0.5 w-4 mb-3 rounded transition-colors duration-300",
                  isPast ? "bg-primary/60" : "bg-muted"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

export { PHASES, PHASE_ORDER, getPhaseIndex };
