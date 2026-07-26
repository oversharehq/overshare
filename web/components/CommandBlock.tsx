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
    <div className="group/cmd relative bg-plate p-4 pr-16">
      <pre className="overflow-x-auto font-mono text-[0.8rem] leading-[1.8] text-paper">
        {lines.map((line) => (
          <div key={line}>
            <span className="mr-1.5 select-none text-flag">$</span>
            {line}
          </div>
        ))}
      </pre>
      <button
        type="button"
        onClick={copy}
        className="label absolute top-3 right-3 border border-mute/60 px-2 py-1 text-faint transition-colors hover:border-paper hover:text-paper"
      >
        {copied ? "Copied" : label}
      </button>
    </div>
  );
}
