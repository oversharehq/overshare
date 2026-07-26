import { BRAND } from "@/lib/brand";
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
      className="group scroll-mt-6 border-b border-rule"
    >
      <summary className="flex cursor-pointer list-none items-start gap-4 py-4 [&::-webkit-details-marker]:hidden">
        {/* The severity bar runs the full height of the row, so the list can be
            skimmed down the left edge without reading a single label. */}
        <span
          className={`mt-1 h-8 w-[3px] shrink-0 ${style.bar}`}
          aria-hidden
        />
        <div className="min-w-0 flex-1">
          <SeverityChip severity={finding.severity} />
          <h3 className="mt-1.5 text-[1.05rem] leading-snug font-medium text-ink transition-colors group-hover:text-flag">
            {finding.title}
          </h3>
          <p className="mt-1 flex flex-wrap items-center gap-x-3 font-mono text-xs text-mute">
            <span>{finding.check_id}</span>
            {finding.confidence === "probable" && (
              <span className="border-l border-rule-firm pl-3 text-ochre">
                needs confirmation
              </span>
            )}
          </p>
        </div>
        <span className="label shrink-0 pt-1 text-faint transition-colors group-open:text-flag">
          <span className="group-open:hidden">+</span>
          <span className="hidden group-open:inline">&minus;</span>
        </span>
      </summary>

      <div className="pb-5 pl-7 text-[0.95rem]">
        <p className="max-w-[34rem] leading-[1.65] text-ink-soft">
          {finding.detail}
        </p>

        {finding.confidence === "probable" && (
          <p className="mt-3 max-w-[34rem] border-l-2 border-ochre bg-ochre-wash px-3 py-2 font-mono text-xs leading-[1.6] text-ochre">
            This one matched a pattern rather than being confirmed outright.
            Check it before acting on it.
          </p>
        )}

        {finding.evidence && (
          <div className="mt-5">
            <p className="label text-faint">Evidence</p>
            <pre className="mt-1.5 overflow-x-auto bg-plate px-3 py-2.5 font-mono text-xs text-paper">
              {finding.evidence}
            </pre>
            <p className="mt-1.5 font-mono text-[0.7rem] text-faint">
              Secrets are truncated. {BRAND.name} never stores or displays a
              full credential.
            </p>
          </div>
        )}

        {finding.location && (
          <div className="mt-5">
            <p className="label text-faint">Where</p>
            <p className="mt-1.5 break-all font-mono text-xs text-ink">
              {finding.location}
            </p>
          </div>
        )}

        {finding.remediation && (
          <div className="mt-5 max-w-[34rem] border-l-2 border-rule-firm bg-inset px-4 py-3">
            <p className="label text-mute">How to fix</p>
            <p className="mt-1.5 leading-[1.6] text-ink">
              {finding.remediation}
            </p>
          </div>
        )}

        {finding.fix_available && !finding.fix && <LockedFix finding={finding} />}
      </div>
    </details>
  );
}

function LockedFix({ finding }: { finding: Finding }) {
  return (
    <div className="print-hidden mt-4 max-w-[34rem] border border-dashed border-rule-firm px-4 py-3">
      <p className="label text-faint">Ready-to-apply fix</p>
      <p className="mt-1.5 leading-[1.6] text-mute">
        {fixTeaser(finding.check_id)} Available on a paid scan, with the change
        written against your app rather than a generic example.
      </p>
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
