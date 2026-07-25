"use client";

import { useState } from "react";

export function CommandBlock({
  lines,
  label = "Copy",
}: {
  lines: string[];
  label?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(lines.join("\n"));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard is unavailable over plain http or when permission is denied.
      // The command is visible and selectable, so there is nothing to recover.
    }
  }

  return (
    <div className="relative rounded-md border border-slate-800 bg-slate-900 p-4">
      <pre className="overflow-x-auto font-mono text-sm leading-relaxed text-slate-100">
        {lines.map((line) => (
          <div key={line}>
            <span className="select-none text-slate-500">$ </span>
            {line}
          </div>
        ))}
      </pre>
      <button
        type="button"
        onClick={copy}
        className="absolute right-2 top-2 rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs font-medium text-slate-300 hover:bg-slate-700"
      >
        {copied ? "Copied" : label}
      </button>
    </div>
  );
}
