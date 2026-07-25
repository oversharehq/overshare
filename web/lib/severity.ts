import type { Grade, Severity } from "./types";

// Tailwind scans source for complete class strings, so these are written out in
// full rather than composed at runtime.
export interface SeverityStyle {
  label: string;
  chip: string;
  dot: string;
  accent: string;
  bar: string;
}

export const SEVERITY_ORDER: Severity[] = [
  "critical",
  "high",
  "medium",
  "low",
  "info",
];

export const SEVERITY_STYLES: Record<Severity, SeverityStyle> = {
  critical: {
    label: "Critical",
    chip: "bg-red-50 text-red-700 ring-red-600/20",
    dot: "bg-red-600",
    accent: "border-l-red-600",
    bar: "bg-red-600",
  },
  high: {
    label: "High",
    chip: "bg-orange-50 text-orange-700 ring-orange-600/20",
    dot: "bg-orange-500",
    accent: "border-l-orange-500",
    bar: "bg-orange-500",
  },
  medium: {
    label: "Medium",
    chip: "bg-amber-50 text-amber-800 ring-amber-600/20",
    dot: "bg-amber-500",
    accent: "border-l-amber-500",
    bar: "bg-amber-500",
  },
  low: {
    label: "Low",
    chip: "bg-sky-50 text-sky-700 ring-sky-600/20",
    dot: "bg-sky-500",
    accent: "border-l-sky-500",
    bar: "bg-sky-500",
  },
  info: {
    label: "Info",
    chip: "bg-slate-100 text-slate-600 ring-slate-500/20",
    dot: "bg-slate-400",
    accent: "border-l-slate-300",
    bar: "bg-slate-400",
  },
};

export const GRADE_STYLES: Record<Grade, { ring: string; text: string; bg: string }> = {
  A: { ring: "ring-emerald-600/30", text: "text-emerald-700", bg: "bg-emerald-50" },
  B: { ring: "ring-emerald-600/30", text: "text-emerald-700", bg: "bg-emerald-50" },
  C: { ring: "ring-amber-600/30", text: "text-amber-700", bg: "bg-amber-50" },
  D: { ring: "ring-orange-600/30", text: "text-orange-700", bg: "bg-orange-50" },
  F: { ring: "ring-red-600/30", text: "text-red-700", bg: "bg-red-50" },
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
