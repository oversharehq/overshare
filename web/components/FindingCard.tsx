import { SEVERITY_STYLES } from "@/lib/severity";
import type { Finding } from "@/lib/types";
import { SeverityChip } from "./SeverityChip";

export function FindingCard({ finding }: { finding: Finding }) {
  const style = SEVERITY_STYLES[finding.severity];
  const expandedByDefault =
    finding.severity === "critical" || finding.severity === "high";

  return (
    <details
      id={finding.check_id}
      open={expandedByDefault}
      className={`group scroll-mt-6 rounded-md border border-l-4 border-slate-200 bg-white shadow-sm ${style.accent}`}
    >
      <summary className="flex cursor-pointer list-none items-start gap-3 p-4 [&::-webkit-details-marker]:hidden">
        <SeverityChip severity={finding.severity} />
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-slate-900">{finding.title}</h3>
          <p className="mt-0.5 font-mono text-xs text-slate-500">
            {finding.check_id}
            {finding.confidence === "probable" && (
              <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 font-sans text-slate-600">
                needs confirmation
              </span>
            )}
          </p>
        </div>
        <svg
          className="mt-1 h-4 w-4 shrink-0 text-slate-400 transition-transform group-open:rotate-90"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden
        >
          <path d="M6 4l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </summary>

      <div className="border-t border-slate-100 px-4 py-4 text-sm">
        <p className="text-slate-700">{finding.detail}</p>

        {finding.confidence === "probable" && (
          <p className="mt-3 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
            This one matched a pattern rather than being confirmed outright. Check
            it before acting on it.
          </p>
        )}

        {finding.evidence && (
          <div className="mt-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Evidence
            </p>
            <pre className="mt-1 overflow-x-auto rounded border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-xs text-slate-800">
              {finding.evidence}
            </pre>
            <p className="mt-1 text-xs text-slate-400">
              Secrets are truncated. LeakScan never stores or displays a full
              credential.
            </p>
          </div>
        )}

        {finding.location && (
          <div className="mt-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Where
            </p>
            <p className="mt-1 break-all font-mono text-xs text-slate-700">
              {finding.location}
            </p>
          </div>
        )}

        {finding.remediation && (
          <div className="mt-4 rounded border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              How to fix
            </p>
            <p className="mt-1 text-slate-700">{finding.remediation}</p>
          </div>
        )}

        {finding.fix_available && !finding.fix && <LockedFix finding={finding} />}
      </div>
    </details>
  );
}

function LockedFix({ finding }: { finding: Finding }) {
  return (
    <div className="print-hidden mt-4 rounded border border-dashed border-slate-300 bg-white p-3">
      <div className="flex items-start gap-2">
        <svg
          className="mt-0.5 h-4 w-4 shrink-0 text-slate-400"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          aria-hidden
        >
          <rect x="3" y="7" width="10" height="6" rx="1" />
          <path d="M5.5 7V5a2.5 2.5 0 015 0v2" strokeLinecap="round" />
        </svg>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Ready-to-apply fix
          </p>
          <p className="mt-1 text-slate-600">
            {fixTeaser(finding.check_id)} Available on a paid scan, with the change
            written against your app rather than a generic example.
          </p>
        </div>
      </div>
    </div>
  );
}

function fixTeaser(checkId: string): string {
  if (checkId.startsWith("secrets.")) {
    return "The exact files and lines to change, plus a rotation checklist so the leaked key is actually retired.";
  }
  if (checkId === "transport.cors_reflects_origin") {
    return "A replacement CORS configuration for your host, with the allowlist filled in.";
  }
  if (checkId === "transport.missing_csp") {
    return "A Content-Security-Policy built from the scripts your app actually loads, so it does not break on deploy.";
  }
  return "The specific configuration change for your stack.";
}
