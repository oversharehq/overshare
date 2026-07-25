import { SEVERITY_STYLES } from "@/lib/severity";
import type { Severity } from "@/lib/types";

export function SeverityChip({ severity }: { severity: Severity }) {
  const style = SEVERITY_STYLES[severity];
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 rounded px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ring-1 ring-inset ${style.chip}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} aria-hidden />
      {style.label}
    </span>
  );
}
