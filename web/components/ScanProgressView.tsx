"use client";

import { useEffect, useState } from "react";
import type { Scan } from "@/lib/types";

export function ScanProgressView({ scan }: { scan: Scan }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const startedAt = new Date(scan.created_at).getTime();
    const tick = () => setElapsed(Math.floor((Date.now() - startedAt) / 1000));
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [scan.created_at]);

  const progress = scan.progress;
  const percent =
    progress && progress.total > 0
      ? Math.min(100, Math.round((progress.completed / progress.total) * 100))
      : null;

  return (
    <div className="border-t-2 border-ink pt-6">
      <p className="label text-flag">Scan in progress</p>

      <p className="mt-3 break-all font-mono text-sm text-ink">{scan.url}</p>

      <p
        className="mt-6 text-[1.35rem] leading-snug font-medium"
        aria-live="polite"
      >
        {scan.status === "queued" ? "Queued" : (progress?.label ?? "Scanning")}
        <span className="animate-pulse text-flag">…</span>
      </p>

      <div
        className="mt-5 h-[3px] w-full bg-inset"
        role="progressbar"
        aria-valuenow={percent ?? undefined}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Scan progress"
      >
        {percent === null ? (
          <div className="h-full w-1/3 animate-pulse bg-rule-firm" />
        ) : (
          <div
            className="h-full bg-flag transition-all duration-500"
            style={{ width: `${Math.max(percent, 4)}%` }}
          />
        )}
      </div>

      <div className="mt-2.5 flex justify-between font-mono text-xs text-mute">
        <span>
          {progress
            ? `Step ${progress.completed + 1} of ${progress.total}`
            : "Starting"}
        </span>
        <span className="tabular-nums">{elapsed}s elapsed</span>
      </div>

      <p className="mt-8 max-w-[34rem] border-t border-rule pt-4 text-[0.95rem] leading-[1.6] text-mute">
        This usually takes under a minute. You can leave this page open — the
        result stays at this URL.
      </p>
    </div>
  );
}
