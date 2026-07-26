import { SEVERITY_STYLES } from "@/lib/severity";
import type { Severity } from "@/lib/types";

export function SeverityChip({ severity }: { severity: Severity }) {
  const style = SEVERITY_STYLES[severity];
  return (
    <span
      className={`label inline-flex shrink-0 items-center gap-2 ${style.text} ${style.weight}`}
    >
      <span className={`h-3 w-[3px] ${style.bar}`} aria-hidden />
      {style.label}
    </span>
  );
}
