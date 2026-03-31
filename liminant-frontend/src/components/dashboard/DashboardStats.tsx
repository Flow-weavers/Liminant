"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useStore } from "@/lib/store";

interface SessionSummary {
  id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  artifact_count: number;
  state: { phase: string };
}

export function DashboardStats() {
  const { sessions, loadSessions } = useStore();
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState("");

  const totalMessages = sessions.reduce((sum, s) => sum + (s.messages?.length || 0), 0);
  const totalArtifacts = sessions.reduce((sum, s) => sum + (s.artifacts?.length || 0), 0);
  const phases = sessions.reduce((acc, s) => {
    acc[s.state?.phase || "unknown"] = (acc[s.state?.phase || "unknown"] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const handleExport = async () => {
    setExporting(true);
    try {
      const sessionData = await Promise.all(
        sessions.map(async (s) => {
          const full = await api.sessions.get(s.id);
          const msgs = await api.sessions.getMessages(s.id);
          return { ...full, messages: msgs.messages };
        })
      );
      const blob = new Blob([JSON.stringify({ sessions: sessionData, exported_at: new Date().toISOString() }, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `liminal-export-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export failed:", e);
    }
    setExporting(false);
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportError("");
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      if (!data.sessions || !Array.isArray(data.sessions)) {
        setImportError("Invalid export file format.");
        return;
      }
      for (const sess of data.sessions) {
        await api.sessions.create({
          working_directory: sess.context?.working_directory,
          language: sess.context?.language,
        });
      }
      await loadSessions();
    } catch (err) {
      setImportError("Failed to parse import file.");
    }
    setImporting(false);
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
        <div className="text-2xl font-bold text-zinc-100">{sessions.length}</div>
        <div className="text-xs text-zinc-500 uppercase tracking-wider">Sessions</div>
      </div>
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
        <div className="text-2xl font-bold text-zinc-100">{totalMessages}</div>
        <div className="text-xs text-zinc-500 uppercase tracking-wider">Messages</div>
      </div>
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
        <div className="text-2xl font-bold text-zinc-100">{totalArtifacts}</div>
        <div className="text-xs text-zinc-500 uppercase tracking-wider">Artifacts</div>
      </div>
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
        <div className="text-xs text-zinc-400 font-mono">
          {Object.entries(phases).map(([phase, count]) => (
            <div key={phase} className="flex justify-between">
              <span className="capitalize">{phase}</span>
              <span className="text-zinc-600">{count}</span>
            </div>
          ))}
        </div>
        <div className="text-xs text-zinc-500 uppercase tracking-wider mt-1">Phases</div>
      </div>

      <div className="col-span-2 md:col-span-4 flex gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={handleExport}
          disabled={exporting}
          className="border-zinc-700 text-zinc-400 hover:text-zinc-200 hover:border-zinc-600"
        >
          {exporting ? "Exporting..." : "Export Sessions"}
        </Button>
        <label className="border border-zinc-700 text-zinc-400 hover:text-zinc-200 hover:border-zinc-600 text-xs px-3 py-1.5 rounded transition-colors cursor-pointer inline-flex items-center">
          <input type="file" accept=".json" onChange={handleImport} className="hidden" />
          {importing ? "Importing..." : "Import Sessions"}
        </label>
        {importError && <span className="text-xs text-red-500 self-center">{importError}</span>}
      </div>
    </div>
  );
}
