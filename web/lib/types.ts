// Mirrors API_CONTRACT.md at the repo root. Change the contract first, then this file.

export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type Confidence = "certain" | "probable";
export type ScanStatus = "queued" | "running" | "complete" | "failed";
export type ScanTier = "passive" | "anon_read" | "authenticated";
export type Grade = "A" | "B" | "C" | "D" | "F";

export interface Fix {
  kind: "sql" | "patch" | "config";
  language: string;
  content: string;
  validated: boolean;
}

export interface Finding {
  check_id: string;
  severity: Severity;
  confidence: Confidence;
  title: string;
  detail: string;
  evidence: string;
  location: string | null;
  /** Generic guidance. Free tier. */
  remediation: string | null;
  /** App-specific generated fix. Paid tier, always null in M3. */
  fix: Fix | null;
  fix_available: boolean;
}

export interface Platform {
  backend?: string;
  project_ref?: string;
  api_url?: string;
  project_id?: string;
  deployment?: string;
  builder?: string;
  framework?: string;
  host?: string;
}

export type SeverityCounts = Record<Severity, number>;

export interface ScanResult {
  url: string;
  score: number;
  grade: Grade;
  counts: SeverityCounts;
  platform: Platform;
  findings: Finding[];
  assets_scanned: string[];
  errors: string[];
  duration_seconds: number;
}

export interface ScanProgress {
  phase: string;
  label: string;
  completed: number;
  total: number;
}

export interface ApiErrorBody {
  code: string;
  message: string;
}

export interface Scan {
  id: string;
  status: ScanStatus;
  url: string;
  tier: ScanTier;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  progress: ScanProgress | null;
  result: ScanResult | null;
  error: ApiErrorBody | null;
  poll_after_ms: number;
}

export function isTerminal(status: ScanStatus): boolean {
  return status === "complete" || status === "failed";
}
