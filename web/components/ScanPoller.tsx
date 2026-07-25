"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiRequestError, getScan } from "@/lib/api";
import { isTerminal, type Scan } from "@/lib/types";
import { ReportView } from "./ReportView";
import { ScanProgressView } from "./ScanProgressView";

export function ScanPoller({ id }: { id: string }) {
  const [scan, setScan] = useState<Scan | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const next = await getScan(id);
        if (cancelled) return;
        setScan(next);
        if (!isTerminal(next.status)) {
          timer = setTimeout(poll, Math.max(next.poll_after_ms, 500));
        }
      } catch (err) {
        if (cancelled) return;
        setError(
          err instanceof ApiRequestError
            ? err.message
            : "Could not load this scan.",
        );
      }
    }

    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [id]);

  if (error) {
    return <Failure title="This scan could not be loaded" message={error} />;
  }

  if (!scan) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
        <div className="h-3 w-40 animate-pulse rounded bg-slate-200" />
        <div className="mt-4 h-3 w-64 animate-pulse rounded bg-slate-100" />
      </div>
    );
  }

  if (scan.status === "failed") {
    return (
      <Failure
        title="The scan could not be completed"
        message={
          scan.error?.message ??
          "The target could not be reached. Check the URL is publicly accessible and try again."
        }
      />
    );
  }

  if (scan.status === "complete" && scan.result) {
    return <ReportView scan={scan} result={scan.result} />;
  }

  return <ScanProgressView scan={scan} />;
}

function Failure({ title, message }: { title: string; message: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
      <h1 className="text-lg font-semibold text-slate-900">{title}</h1>
      <p className="mt-2 text-sm text-slate-600">{message}</p>
      <Link
        href="/"
        className="mt-6 inline-block rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700"
      >
        Start a new scan
      </Link>
    </div>
  );
}
