"use client";

interface CodeBlockProps {
  code: string;
  language?: string;
  showDiff?: boolean;
}

export function CodeBlock({ code, language, showDiff }: CodeBlockProps) {
  const lines = code.split("\n");
  const lang = language || "text";

  if (showDiff) {
    return (
      <div className="bg-zinc-950 border border-zinc-800 rounded-lg overflow-hidden">
        <div className="flex items-center justify-between px-3 py-1.5 bg-zinc-900 border-b border-zinc-800">
          <span className="text-[10px] font-mono text-zinc-500">{lang}</span>
          <span className="text-[10px] text-zinc-600">diff</span>
        </div>
        <pre className="font-mono text-xs p-3 overflow-x-auto">
          {lines.map((line, i) => {
            let cls = "text-zinc-300";
            if (line.startsWith("+++") || line.startsWith("+")) cls = "text-green-400";
            if (line.startsWith("---") || line.startsWith("-")) cls = "text-red-400";
            if (line.startsWith("@@")) cls = "text-yellow-500";
            return (
              <div key={i} className={cls}>
                {line || " "}
              </div>
            );
          })}
        </pre>
      </div>
    );
  }

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-3 py-1.5 bg-zinc-900 border-b border-zinc-800">
        <span className="text-[10px] font-mono text-zinc-500">{lang}</span>
        <span className="text-[10px] text-zinc-600">{lines.length}L</span>
      </div>
      <pre className="font-mono text-xs p-3 overflow-x-auto">
        {lines.map((line, i) => (
          <div key={i} className="text-zinc-300">
            {line || " "}
          </div>
        ))}
      </pre>
    </div>
  );
}
