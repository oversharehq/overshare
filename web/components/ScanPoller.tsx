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
      <div className="border-t-2 border-ink pt-6">
        <div className="h-2.5 w-40 animate-pulse bg-inset" />
        <div className="mt-4 h-2.5 w-64 animate-pulse bg-inset" />
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
    <div className="border-t-2 border-flag pt-6">
      <p className="label text-flag">Scan failed</p>
      <h1 className="mt-3 text-[1.6rem] leading-tight font-medium">{title}</h1>
      <p className="mt-3 max-w-[34rem] text-[0.95rem] leading-[1.6] text-ink-soft">
        {message}
      </p>
      <Link
        href="/"
        className="label mt-7 inline-block bg-ink px-5 py-3 text-paper transition-colors hover:bg-flag"
      >
        Start a new scan →
      </Link>
    </div>
  );
}
