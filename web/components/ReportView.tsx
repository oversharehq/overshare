"use client";

import Link from "next/link";
import type { Scan, ScanResult } from "@/lib/types";
import { FindingsList } from "./FindingsList";
import { PlatformPanel } from "./PlatformPanel";
import { ScopeNotice } from "./ScopeNotice";
import { ScoreCard } from "./ScoreCard";

export function ReportView({ scan, result }: { scan: Scan; result: ScanResult }) {
  const completed = scan.completed_at ? new Date(scan.completed_at) : null;
  const fixable = result.findings.filter((finding) => finding.fix_available).length;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Scan report
          </p>
          <h1 className="mt-1 break-all text-xl font-semibold text-slate-900">
            {result.url}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            {completed && (
              <time dateTime={completed.toISOString()}>
                {completed.toLocaleString()}
              </time>
            )}
            {completed && " · "}
            Completed in {result.duration_seconds}s · Passive scan
          </p>
        </div>

        <button
          type="button"
          onClick={() => window.print()}
          className="print-hidden rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
        >
          Save as PDF
        </button>
      </div>

      <ScoreCard result={result} />
      <PlatformPanel platform={result.platform} />
      <FindingsList findings={result.findings} />
      <ScopeNotice result={result} />

      {fixable > 0 && (
        <section className="print-hidden mt-8 rounded-lg border border-slate-900 bg-slate-900 p-6 text-white">
          <h2 className="text-base font-semibold">
            {fixable} of these have a fix we can write for you
          </h2>
          <p className="mt-2 max-w-2xl text-sm text-slate-300">
            A paid scan turns each finding into the actual change for your app —
            the policy, the header, the config — plus a re-scan that verifies the
            fix landed, and a report you can hand to a customer asking about
            security.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              disabled
              className="cursor-not-allowed rounded-md bg-white px-4 py-2 text-sm font-semibold text-slate-900 opacity-60"
            >
              Coming soon
            </button>
            <Link
              href="/"
              className="rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-800"
            >
              Scan another app
            </Link>
          </div>
        </section>
      )}
    </div>
  );
}
