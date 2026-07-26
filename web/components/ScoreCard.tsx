import {
  GRADE_STYLES,
  SEVERITY_ORDER,
  SEVERITY_STYLES,
  gradeSummary,
} from "@/lib/severity";
import type { ScanResult } from "@/lib/types";

export function ScoreCard({ result }: { result: ScanResult }) {
  const grade = GRADE_STYLES[result.grade];

  return (
    <section>
      <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:gap-8">
        <div
          className={`grid h-28 w-24 shrink-0 place-items-center border ${grade.rule}`}
        >
          <span
            className={`text-[4.5rem] leading-none font-medium ${grade.text}`}
          >
            {result.grade}
          </span>
        </div>

        <div className="min-w-0 flex-1">
          <p className="label text-faint">Score</p>
          <p className="mt-1.5 font-mono text-2xl tabular-nums text-ink">
            {result.score}
            <span className="text-faint"> / 100</span>
          </p>

          {/* A scale rather than a progress bar: the tick marks where this app
              landed on a range, which is what a score actually is. */}
          <div className="relative mt-3 h-3 max-w-xs border-l border-r border-rule-firm">
            <div className="absolute top-1/2 h-px w-full bg-rule" />
            <div
              className="absolute top-0 h-3 w-[2px] bg-flag"
              style={{ left: `calc(${result.score}% - 1px)` }}
            />
          </div>

          <p className="mt-4 max-w-lg text-[1.05rem] leading-[1.55] text-ink">
            {gradeSummary(result.grade, result.counts)}
          </p>
        </div>
      </div>

      <dl className="mt-8 grid grid-cols-2 border-t border-rule sm:grid-cols-5">
        {SEVERITY_ORDER.map((severity) => {
          const count = result.counts[severity];
          const style = SEVERITY_STYLES[severity];
          const present = count > 0;
          return (
            <div
              key={severity}
              className="flex items-baseline gap-2.5 border-b border-rule py-3 sm:block sm:border-b-0 sm:border-r sm:px-3 sm:last:border-r-0 sm:first:pl-0"
            >
              <dt
                className={`label flex items-center gap-2 ${
                  present ? style.text : "text-faint"
                }`}
              >
                <span
                  className={`h-2.5 w-[3px] ${present ? style.bar : "bg-rule"}`}
                  aria-hidden
                />
                {style.label}
              </dt>
              <dd
                className={`font-mono text-xl tabular-nums sm:mt-2 ${
                  present ? "text-ink" : "text-faint"
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
