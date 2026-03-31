"use client";
import { useEffect, useState } from "react";

interface ArtifactChange {
  type: "create" | "modify" | "delete";
  description: string;
  diff: string;
}

interface Artifact {
  id: string;
  session_id: string;
  path: string;
  type: string;
  summary: string;
  content_hash: string;
  size_bytes: number;
  created_at: string;
}

interface ArtifactDetail extends Artifact {
  versions?: Array<{ content_hash: string; path: string; created_at: string }>;
}

function DiffView({ diff }: { diff: string }) {
  const lines = diff.split("\n");
  return (
    <div className="font-mono text-xs overflow-x-auto">
      {lines.map((line, i) => {
        let cls = "text-zinc-400";
        if (line.startsWith("+++") || line.startsWith("+")) cls = "text-green-400";
        if (line.startsWith("---") || line.startsWith("-")) cls = "text-red-400";
        if (line.startsWith("@@")) cls = "text-yellow-500";
        return (
          <div key={i} className={cls}>
            {line}
          </div>
        );
      })}
    </div>
  );
}

export function ArtifactsPanel({ sessionId }: { sessionId: string }) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selected, setSelected] = useState<ArtifactDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!sessionId) return;
    setLoading(true);
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/artifacts/session/${sessionId}`)
      .then((r) => r.json())
      .then((d) => { setArtifacts(d.artifacts || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [sessionId]);

  const loadDetail = async (art: Artifact) => {
    const r = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/artifacts/${art.id}`);
    const d = await r.json();
    setSelected({ ...art, ...d.meta });
  };

  if (loading) return <div className="text-sm text-zinc-500 p-4">Loading artifacts...</div>;
  if (artifacts.length === 0) {
    return <div className="text-sm text-zinc-500 p-4">No artifacts generated in this session.</div>;
  }

  return (
    <div className="flex flex-col h-full">
      <div className="border-b p-3">
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
          Artifacts ({artifacts.length})
        </h3>
      </div>
      <div className="flex-1 overflow-y-auto">
        {artifacts.map((art) => (
          <button
            key={art.id}
            onClick={() => loadDetail(art)}
            className={`w-full text-left px-3 py-2 border-b border-zinc-800 hover:bg-zinc-800 transition-colors ${
              selected?.id === art.id ? "bg-zinc-800" : ""
            }`}
          >
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${
                art.type === "code" ? "bg-blue-500" :
                art.type === "file" ? "bg-green-500" : "bg-zinc-500"
              }`} />
              <span className="text-xs font-mono text-zinc-300 truncate">{art.path}</span>
            </div>
            <div className="text-[10px] text-zinc-600 mt-0.5 truncate">{art.summary || "No summary"}</div>
          </button>
        ))}
      </div>

      {selected && (
        <div className="border-t bg-zinc-950 max-h-64 overflow-y-auto">
          <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800">
            <span className="text-xs font-mono text-zinc-400">{selected.path}</span>
            <button
              onClick={() => setSelected(null)}
              className="text-zinc-600 hover:text-zinc-400 text-xs"
            >
              ✕
            </button>
          </div>
          <div className="p-3 space-y-2">
            <div className="flex gap-4 text-[10px] text-zinc-500">
              <span>{selected.type}</span>
              <span>{(selected.size_bytes / 1024).toFixed(1)} KB</span>
              <span>{new Date(selected.created_at).toLocaleTimeString()}</span>
            </div>
            {selected.versions && selected.versions.length > 0 && (
              <div>
                <div className="text-[10px] font-semibold text-zinc-600 uppercase mb-1">
                  Version History ({selected.versions.length})
                </div>
                {selected.versions.map((v, i) => (
                  <div key={i} className="text-[10px] text-zinc-600 font-mono">
                    {v.created_at} — {v.content_hash}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
