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
    <div className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="relative flex h-3 w-3" aria-hidden>
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-slate-400 opacity-75" />
          <span className="relative inline-flex h-3 w-3 rounded-full bg-slate-600" />
        </span>
        <p className="text-sm font-medium text-slate-900" aria-live="polite">
          {scan.status === "queued"
            ? "Queued"
            : (progress?.label ?? "Scanning")}
        </p>
      </div>

      <p className="mt-2 break-all font-mono text-sm text-slate-500">{scan.url}</p>

      <div
        className="mt-6 h-1.5 overflow-hidden rounded-full bg-slate-100"
        role="progressbar"
        aria-valuenow={percent ?? undefined}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Scan progress"
      >
        {percent === null ? (
          <div className="h-full w-1/3 animate-pulse rounded-full bg-slate-400" />
        ) : (
          <div
            className="h-full rounded-full bg-slate-900 transition-all duration-500"
            style={{ width: `${Math.max(percent, 4)}%` }}
          />
        )}
      </div>

      <div className="mt-3 flex justify-between text-xs text-slate-500">
        <span>
          {progress ? `Step ${progress.completed + 1} of ${progress.total}` : "Starting"}
        </span>
        <span className="tabular-nums">{elapsed}s elapsed</span>
      </div>

      <p className="mt-6 border-t border-slate-100 pt-4 text-xs text-slate-500">
        This usually takes under a minute. You can leave this page open — the
        result stays at this URL.
      </p>
    </div>
  );
}
