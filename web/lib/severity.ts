import type { Grade, Severity } from "./types";

// Tailwind scans source for complete class strings, so these are written out in
// full rather than composed at runtime.
export interface SeverityStyle {
  label: string;
  /** Text colour for the mono severity label. */
  text: string;
  /** The vertical bar that carries severity in lists and cards. */
  bar: string;
  /** Weight of the label, so severity survives being read in greyscale. */
  weight: string;
}

export const SEVERITY_ORDER: Severity[] = [
  "critical",
  "high",
  "medium",
  "low",
  "info",
];

/**
 * Severity is encoded as weight plus a rule, in two hues rather than five.
 *
 * A five-colour scale trains people to read the palette instead of the finding,
 * and it makes a medium look like an emergency on a page that is otherwise ink
 * on paper. Vermilion is reserved for the two severities that should stop a
 * deploy; medium is ochre; low and info are plain ink at decreasing weight.
 */
export const SEVERITY_STYLES: Record<Severity, SeverityStyle> = {
  critical: {
    label: "Critical",
    text: "text-flag",
    bar: "bg-flag",
    weight: "font-semibold",
  },
  high: {
    label: "High",
    text: "text-flag",
    bar: "bg-flag/55",
    weight: "font-medium",
  },
  medium: {
    label: "Medium",
    text: "text-ochre",
    bar: "bg-ochre/70",
    weight: "font-medium",
  },
  low: {
    label: "Low",
    text: "text-mute",
    bar: "bg-rule-firm",
    weight: "font-medium",
  },
  info: {
    label: "Info",
    text: "text-faint",
    bar: "bg-rule",
    weight: "font-normal",
  },
};

export const GRADE_STYLES: Record<Grade, { text: string; rule: string }> = {
  A: { text: "text-pass", rule: "border-pass/40" },
  B: { text: "text-pass", rule: "border-pass/40" },
  C: { text: "text-ochre", rule: "border-ochre/40" },
  D: { text: "text-ochre", rule: "border-ochre/50" },
  F: { text: "text-flag", rule: "border-flag/50" },
};

/** Headline shown beside the score. Leads with consequence, not alarm. */
export function gradeSummary(grade: Grade, counts: Record<Severity, number>): string {
  if (counts.critical > 0) {
    return "Critical exposure found — anyone can reach data or keys they shouldn't.";
  }
  if (counts.high > 0) {
    return "Serious issues found that a security review would flag.";
  }
  if (grade === "A" || grade === "B") {
    return "No serious exposure found on the public surface.";
  }
  return "Hardening gaps found. Nothing critical on the public surface.";
}
