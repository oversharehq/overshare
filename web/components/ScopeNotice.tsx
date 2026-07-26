import type { ScanResult } from "@/lib/types";
import { Block } from "./Paper";

/**
 * Overshare reports only what it can prove, which means it under-reports by
 * design. Saying so plainly is the difference between a scanner people trust and
 * one that quietly implies "no findings" means "secure".
 */
export function ScopeNotice({ result }: { result: ScanResult }) {
  const notChecked = [
    result.platform.backend === "supabase"
      ? "Whether Row Level Security is actually enforced on your Supabase tables"
      : "Whether your database enforces per-user access rules",
    "Anything behind a login",
    "Server-side code and environment variables",
    "Known vulnerabilities in your dependencies",
  ];

  return (
    <>
      {result.errors.length > 0 && (
        <div className="mt-8 border-l-2 border-ochre bg-ochre-wash px-4 py-3">
          <p className="label text-ochre">Some checks did not complete</p>
          <p className="mt-1.5 text-[0.95rem] leading-[1.6] text-ochre">
            These did not run, so treat them as unknown rather than passed.
          </p>
          <ul className="mt-2 space-y-1 font-mono text-xs text-ochre">
            {result.errors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      <Block index="04" title="What this scan did not cover">
        <ul className="max-w-[34rem] border-t border-rule">
          {notChecked.map((item) => (
            <li
              key={item}
              className="flex gap-3 border-b border-rule py-2.5 text-[0.95rem] leading-[1.5] text-ink-soft"
            >
              <span className="label shrink-0 pt-1 text-faint">not checked</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 max-w-[34rem] text-[0.95rem] leading-[1.6] text-mute">
          A clean result here means nothing dangerous is exposed on the public
          surface. It is not a statement about the app as a whole.
        </p>

        <details className="group mt-6">
          <summary className="label flex cursor-pointer list-none items-center gap-2 text-mute transition-colors hover:text-flag [&::-webkit-details-marker]:hidden">
            <span className="text-faint">
              <span className="group-open:hidden">+</span>
              <span className="hidden group-open:inline">&minus;</span>
            </span>
            {result.assets_scanned.length} resources fetched
          </summary>
          <ul className="mt-3 space-y-1 border-l border-rule pl-4">
            {result.assets_scanned.map((asset) => (
              <li key={asset} className="break-all font-mono text-xs text-mute">
                {asset}
              </li>
            ))}
          </ul>
        </details>
      </Block>
    </>
  );
}
