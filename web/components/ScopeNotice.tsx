import type { ScanResult } from "@/lib/types";

/**
 * LeakScan reports only what it can prove, which means it under-reports by
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
    <section className="mt-8 space-y-4">
      {result.errors.length > 0 && (
        <div className="rounded-md border border-amber-300 bg-amber-50 p-4">
          <h2 className="text-sm font-semibold text-amber-900">
            Some checks did not complete
          </h2>
          <p className="mt-1 text-sm text-amber-900">
            These did not run, so treat them as unknown rather than passed.
          </p>
          <ul className="mt-2 list-inside list-disc space-y-1 font-mono text-xs text-amber-900">
            {result.errors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-900">
          What this scan did not cover
        </h2>
        <ul className="mt-2 space-y-1.5 text-sm text-slate-600">
          {notChecked.map((item) => (
            <li key={item} className="flex gap-2">
              <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-slate-300" aria-hidden />
              {item}
            </li>
          ))}
        </ul>
        <p className="mt-3 text-xs text-slate-500">
          A clean result here means nothing dangerous is exposed on the public
          surface. It is not a statement about the app as a whole.
        </p>

        <details className="mt-4 border-t border-slate-100 pt-3">
          <summary className="cursor-pointer text-xs font-medium text-slate-600 hover:text-slate-900">
            {result.assets_scanned.length} resources fetched
          </summary>
          <ul className="mt-2 space-y-1">
            {result.assets_scanned.map((asset) => (
              <li key={asset} className="break-all font-mono text-xs text-slate-500">
                {asset}
              </li>
            ))}
          </ul>
        </details>
      </div>
    </section>
  );
}
