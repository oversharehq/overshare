/**
 * The factual spine of /methodology and /acceptable-use.
 *
 * These pages restate documents that also live at the repo root, and the web
 * image builds from `web/` alone so it cannot read them at build time. Prose is
 * therefore written for the web in the page files, but every heading and every
 * load-bearing number lives here, and `tests/test_docs_sync.py` fails CI if any
 * of it drifts from METHODOLOGY.md, ACCEPTABLE_USE.md, or the scanner's own
 * penalties, grade thresholds and retention default.
 *
 * Anything a reader could act on belongs in this file. Anything that is only
 * phrasing does not.
 */

/** Mirrors the `##` headings of METHODOLOGY.md, in order. */
export const METHODOLOGY_SECTIONS = [
  "The one rule",
  'What "provable" means',
  "Severity, and what each level means",
  "What it does not do",
  "Known blind spots",
  "Measured false-positive rate",
  "Reporting a false positive",
  "Reproducing any of this",
] as const;

/** Mirrors the `##` headings of ACCEPTABLE_USE.md, in order. */
export const ACCEPTABLE_USE_SECTIONS = [
  "The short version",
  "What the scanner does by default",
  "Scan tiers and what each requires",
  "Prohibited",
  "If you find something in someone else's application",
  "What we do with scans submitted to the hosted service",
  "Enforcement",
  "Questions",
] as const;

export interface SeverityLevel {
  level: string;
  meaning: string;
  example: string;
  penalty: number;
}

/** Penalties are subtracted from 100 once per check, never once per occurrence. */
export const SEVERITY_LEVELS: SeverityLevel[] = [
  {
    level: "Critical",
    meaning:
      "A credential or access path that is exploitable right now, by anyone, with no further work.",
    example: "A live service_role key. A readable /.env.",
    penalty: 40,
  },
  {
    level: "High",
    meaning:
      "A serious weakness that needs a specific additional condition to be exploited, or exposes source and internals rather than access.",
    example: "Published source maps. A readable /.git/config.",
    penalty: 20,
  },
  {
    level: "Medium",
    meaning:
      "A real weakness that raises the cost of other attacks or widens their impact.",
    example: "Missing CSP. CORS reflecting arbitrary origins.",
    penalty: 8,
  },
  {
    level: "Low",
    meaning:
      "Hardening that is absent. Individually minor, and honestly labelled as such.",
    example: "Missing nosniff. Missing Referrer-Policy.",
    penalty: 3,
  },
  {
    level: "Info",
    meaning: "Observed and reported, not a problem.",
    example: "Platform fingerprint. The Supabase anon key. DNS records.",
    penalty: 0,
  },
];

/** Grade floors, highest first. Anything below the last entry is an F. */
export const GRADE_THRESHOLDS: { grade: string; min: number }[] = [
  { grade: "A", min: 90 },
  { grade: "B", min: 75 },
  { grade: "C", min: 60 },
  { grade: "D", min: 40 },
];

export interface ScanTier {
  tier: string;
  name: string;
  does: string;
  authorisation: string;
  implemented: boolean;
}

export const SCAN_TIERS: ScanTier[] = [
  {
    tier: "A",
    name: "Passive",
    does: "Fetches what the app serves to any visitor.",
    authorisation: "None.",
    implemented: true,
  },
  {
    tier: "B",
    name: "Anon-key read",
    does: "Uses the client-side key the app already ships to every browser, to make the same read any visitor's browser could. This is the Row Level Security check.",
    authorisation:
      "The owner must have submitted the app themselves, or given permission.",
    implemented: false,
  },
  {
    tier: "C",
    name: "Authenticated",
    does: "Owner-supplied credentials, deeper probing.",
    authorisation: "Written owner authorisation. Always. No exceptions.",
    implemented: false,
  },
];

/**
 * How long a stored scan survives. This is a privacy claim made to the public,
 * so CI asserts it equals the scanner's own OVERSHARE_RETENTION_DAYS default.
 */
export const RETENTION_DAYS = 30;

/** Vendor namespaces matched literally, quoted on the methodology page. */
export const VENDOR_PREFIXES = [
  "sk_live_",
  "AKIA",
  "ghp_",
  "github_pat_",
  "SG.",
  "xoxb-",
] as const;
