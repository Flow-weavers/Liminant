"use client";
import { useEffect, useState } from "react";

interface TimelineEvent {
  id: string;
  timestamp: string;
  event_type: string;
  description: string;
  metadata: Record<string, unknown>;
}

interface TimelineData {
  session_id: string;
  events: TimelineEvent[];
  total_events: number;
}

const EVENT_COLORS: Record<string, string> = {
  message: "bg-blue-500",
  artifact: "bg-green-500",
  constraint_change: "bg-yellow-500",
  phase_change: "bg-purple-500",
  tool_execution: "bg-orange-500",
};

function formatTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function groupByDate(events: TimelineEvent[]) {
  const grouped: Record<string, TimelineEvent[]> = {};
  for (const e of events) {
    const date = e.timestamp.split("T")[0];
    if (!grouped[date]) grouped[date] = [];
    grouped[date].push(e);
  }
  return grouped;
}

export function SessionTimeline({ sessionId }: { sessionId: string }) {
  const [data, setData] = useState<TimelineData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!sessionId) return;
    setLoading(true);
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/timeline/session/${sessionId}`)
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [sessionId]);

  if (loading) return <div className="text-sm text-zinc-500">Loading timeline...</div>;
  if (!data || data.total_events === 0) {
    return <div className="text-sm text-zinc-500">No events recorded yet.</div>;
  }

  const grouped = groupByDate(data.events);

  return (
    <div className="space-y-4">
      {Object.entries(grouped).map(([date, events]) => (
        <div key={date}>
          <div className="text-xs font-semibold text-zinc-500 uppercase mb-2">{date}</div>
          <div className="relative border-l border-zinc-700 pl-4 space-y-3">
            {events.map((evt) => (
              <div key={evt.id} className="relative">
                <div
                  className={`absolute -left-[17px] w-2.5 h-2.5 rounded-full mt-1.5 ${EVENT_COLORS[evt.event_type] || "bg-zinc-500"}`}
                />
                <div className="flex items-baseline gap-2">
                  <span className="text-[10px] text-zinc-600 font-mono">{formatTime(evt.timestamp)}</span>
                  <span className="text-xs font-medium text-zinc-300">{evt.description}</span>
                </div>
                {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                  <pre className="text-[10px] text-zinc-600 mt-0.5 ml-24 font-mono overflow-x-auto">
                    {JSON.stringify(evt.metadata)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
