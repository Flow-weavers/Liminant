"use client";
import { useState } from "react";
import { api } from "@/lib/api";

interface QuickAddKBProps {
  onAdded?: () => void;
}

export function QuickAddKB({ onAdded }: QuickAddKBProps) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [type, setType] = useState<"rule" | "pattern" | "preference" | "context">("rule");
  const [tags, setTags] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !body.trim()) return;
    setLoading(true);
    try {
      await api.knowledge.create({
        type,
        content: { title: title.trim(), body: body.trim(), examples: [] },
        metadata: {
          tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
          source: "user_defined",
          confidence: 1.0,
          usage_count: 0,
        },
        triggers: { keywords: [title.trim().toLowerCase()], session_types: [], context_patterns: [] },
      });
      setTitle("");
      setBody("");
      setTags("");
      setSuccess(true);
      setTimeout(() => setSuccess(false), 2000);
      onAdded?.();
    } catch (e) {
      console.error("Failed to add KB entry:", e);
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3">
      <div className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Quick Add Knowledge</div>
      <div className="flex gap-2">
        <select
          value={type}
          onChange={(e) => setType(e.target.value as typeof type)}
          className="bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs rounded px-2 py-1"
        >
          <option value="rule">Rule</option>
          <option value="pattern">Pattern</option>
          <option value="preference">Preference</option>
          <option value="context">Context</option>
        </select>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title..."
          className="flex-1 bg-zinc-800 border border-zinc-700 text-zinc-200 text-xs rounded px-2 py-1 placeholder-zinc-600"
        />
      </div>
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Body content..."
        rows={3}
        className="w-full bg-zinc-800 border border-zinc-700 text-zinc-200 text-xs rounded px-2 py-1 resize-none placeholder-zinc-600"
      />
      <div className="flex items-center gap-2">
        <input
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="Tags: tag1, tag2..."
          className="flex-1 bg-zinc-800 border border-zinc-700 text-zinc-200 text-xs rounded px-2 py-1 placeholder-zinc-600"
        />
        <button
          type="submit"
          disabled={loading || !title.trim() || !body.trim()}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-xs px-3 py-1 rounded transition-colors"
        >
          {loading ? "..." : "Add"}
        </button>
      </div>
      {success && <div className="text-[10px] text-green-500">Knowledge entry added.</div>}
    </form>
  );
}
