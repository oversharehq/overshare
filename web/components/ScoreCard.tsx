import { GRADE_STYLES, SEVERITY_ORDER, SEVERITY_STYLES, gradeSummary } from "@/lib/severity";
import type { ScanResult } from "@/lib/types";

export function ScoreCard({ result }: { result: ScanResult }) {
  const grade = GRADE_STYLES[result.grade];

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
        <div
          className={`grid h-24 w-24 shrink-0 place-items-center rounded-lg ring-1 ring-inset ${grade.bg} ${grade.ring}`}
        >
          <span className={`text-5xl font-bold leading-none ${grade.text}`}>
            {result.grade}
          </span>
        </div>

        <div className="min-w-0">
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-semibold text-slate-900">
              {result.score}
            </span>
            <span className="text-sm text-slate-500">out of 100</span>
          </div>
          <p className="mt-1 text-base text-slate-700">
            {gradeSummary(result.grade, result.counts)}
          </p>
        </div>
      </div>

      <dl className="mt-6 grid grid-cols-2 gap-px overflow-hidden rounded-md border border-slate-200 bg-slate-200 sm:grid-cols-5">
        {SEVERITY_ORDER.map((severity) => {
          const count = result.counts[severity];
          const style = SEVERITY_STYLES[severity];
          return (
            <div key={severity} className="bg-white px-3 py-3 text-center">
              <dt className="flex items-center justify-center gap-1.5 text-xs font-medium uppercase tracking-wide text-slate-500">
                <span
                  className={`h-1.5 w-1.5 rounded-full ${count > 0 ? style.dot : "bg-slate-300"}`}
                  aria-hidden
                />
                {style.label}
              </dt>
              <dd
                className={`mt-1 text-xl font-semibold tabular-nums ${
                  count > 0 ? "text-slate-900" : "text-slate-300"
                }`}
              >
                {count}
              </dd>
            </div>
          );
        })}
      </dl>
    </section>
  );
}
