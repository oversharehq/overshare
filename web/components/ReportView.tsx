"use client";

import Link from "next/link";
import { BRAND } from "@/lib/brand";
import type { Scan, ScanResult } from "@/lib/types";
import { FindingsList } from "./FindingsList";
import { Block } from "./Paper";
import { PlatformPanel } from "./PlatformPanel";
import { ScopeNotice } from "./ScopeNotice";
import { ScoreCard } from "./ScoreCard";

export function ReportView({ scan, result }: { scan: Scan; result: ScanResult }) {
  const completed = scan.completed_at ? new Date(scan.completed_at) : null;
  const fixable = result.findings.filter((finding) => finding.fix_available).length;

  return (
    <div>
      {/* Document head. The URL is the title of this report, so it is set as
          one — the rest is filing information in mono. */}
      <header className="border-b-2 border-ink pb-5">
        <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-3">
          <p className="label text-flag">{BRAND.name} scan report</p>
          <button
            type="button"
            onClick={() => window.print()}
            className="label print-hidden border border-rule-firm px-3 py-1.5 text-mute transition-colors hover:border-ink hover:text-ink"
          >
            Save as PDF
          </button>
        </div>

        <h1 className="mt-3 max-w-[38rem] break-all text-[1.7rem] leading-tight font-medium">
          {result.url}
        </h1>

        <dl className="mt-4 flex flex-wrap gap-x-8 gap-y-2 font-mono text-xs text-mute">
          {completed && (
            <div className="flex gap-2">
              <dt className="text-faint">Completed</dt>
              <dd>
                <time dateTime={completed.toISOString()}>
                  {completed.toLocaleString()}
                </time>
              </dd>
            </div>
          )}
          <div className="flex gap-2">
            <dt className="text-faint">Duration</dt>
            <dd className="tabular-nums">{result.duration_seconds}s</dd>
          </div>
          <div className="flex gap-2">
            <dt className="text-faint">Tier</dt>
            <dd>Passive scan</dd>
          </div>
        </dl>
      </header>

      <Block index="01" title="Result">
        <ScoreCard result={result} />
      </Block>

      <PlatformPanel platform={result.platform} />
      <FindingsList findings={result.findings} />
      <ScopeNotice result={result} />

      {fixable > 0 && (
        <section className="print-hidden mt-12 bg-plate p-7">
          <p className="label text-flag">Overshare Cloud</p>
          <h2 className="mt-3 max-w-md text-[1.4rem] leading-snug font-medium text-paper">
            {fixable} of these have a fix we can write for you
          </h2>
          <p className="mt-3 max-w-xl text-[0.95rem] leading-[1.6] text-rule">
            A paid scan turns each finding into the actual change for your app —
            the policy, the header, the config — plus a re-scan that verifies the
            fix landed, and a report you can hand to a customer asking about
            security.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              disabled
              className="label cursor-not-allowed border border-mute/60 px-4 py-2.5 text-faint"
            >
              Coming soon
            </button>
            <Link
              href="/"
              className="label border border-transparent bg-paper px-4 py-2.5 text-plate transition-colors hover:bg-flag hover:text-paper"
            >
              Scan another app →
            </Link>
          </div>
        </section>
      )}
    </div>
  );
}
