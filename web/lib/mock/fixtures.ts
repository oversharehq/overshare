import type { ScanResult } from "../types";

/**
 * Development fixtures only. These are hand-written to exercise the report UI at
 * both ends of the range — they are not scanner output and must never be served
 * in production. See app/api/v1/scans/route.ts for the guard.
 */

const VULNERABLE_FINDINGS: ScanResult["findings"] = [
  {
    check_id: "secrets.supabase_service_role",
    severity: "critical",
    confidence: "certain",
    title: "Supabase service_role key shipped in the client bundle",
    detail:
      "The service_role key was found in JavaScript served to every visitor. This key bypasses Row Level Security entirely and grants full read and write access to every table in the database. Anyone who opens developer tools already has it.",
    evidence: "eyJhbGciO************VqZ0",
    location: "https://taskflow.lovable.app/assets/index-B7xK2p.js",
    remediation:
      "Rotate the key first — the exposed one must be treated as compromised, and rotating it is what actually stops the bleeding. In Supabase go to Settings, API, then regenerate the service_role key. Then remove it from client code entirely: anything that genuinely needs service_role has to run server-side, in an Edge Function or your own backend.",
    fix: null,
    fix_available: true,
  },
  {
    check_id: "secrets.stripe_secret_key",
    severity: "high",
    confidence: "certain",
    title: "Stripe live secret key shipped in the client bundle",
    detail:
      "A key beginning sk_live_ was found in client-side JavaScript. It authorises charges, refunds, and access to customer records on your live Stripe account.",
    evidence: "sk_live_************a91X",
    location: "https://taskflow.lovable.app/assets/index-B7xK2p.js",
    remediation:
      "Roll the key in the Stripe dashboard, then move every Stripe call to a server-side route. Only publishable keys beginning pk_live_ belong in browser code.",
    fix: null,
    fix_available: true,
  },
  {
    check_id: "exposure.source_map",
    severity: "medium",
    confidence: "certain",
    title: "Source map publicly accessible",
    detail:
      "A .map file is served alongside the bundle, which reconstructs your original source including comments, file structure, and any logic you assumed was obscured by minification.",
    evidence: "https://taskflow.lovable.app/assets/index-B7xK2p.js.map",
    location: "https://taskflow.lovable.app/assets/index-B7xK2p.js.map",
    remediation:
      "Disable source map generation for production builds, or upload maps to your error tracker without serving them publicly.",
    fix: null,
    fix_available: false,
  },
  {
    check_id: "transport.cors_reflects_origin",
    severity: "medium",
    confidence: "certain",
    title: "CORS reflects any origin while allowing credentials",
    detail:
      "The server echoed the request's Origin header back in Access-Control-Allow-Origin and also sent Access-Control-Allow-Credentials: true. Any site a logged-in user visits can make authenticated requests to this app and read the responses.",
    evidence: "Access-Control-Allow-Origin: https://leakscan-probe.invalid",
    location: "https://taskflow.lovable.app/",
    remediation:
      "Replace origin reflection with an explicit allowlist of origins you control, and only send Access-Control-Allow-Credentials for those. If no cross-origin browser client needs credentials, drop the header entirely.",
    fix: null,
    fix_available: true,
  },
  {
    check_id: "transport.missing_csp",
    severity: "medium",
    confidence: "certain",
    title: "No Content-Security-Policy header",
    detail:
      "The app sends no Content-Security-Policy. If user-supplied content is ever rendered without escaping, nothing limits what an injected script can load or where it can send data.",
    evidence: "Content-Security-Policy: (absent)",
    location: "https://taskflow.lovable.app/",
    remediation:
      "Start with Content-Security-Policy-Report-Only so you can find what breaks without taking the app down, then enforce once the report is quiet.",
    fix: null,
    fix_available: true,
  },
  {
    check_id: "transport.missing_nosniff",
    severity: "low",
    confidence: "certain",
    title: "X-Content-Type-Options header not set",
    detail:
      "Without nosniff, a browser may disregard the declared content type and infer its own, which can turn a file you serve as data into a file it executes as script.",
    evidence: "X-Content-Type-Options: (absent)",
    location: "https://taskflow.lovable.app/",
    remediation: "Send X-Content-Type-Options: nosniff on all responses.",
    fix: null,
    fix_available: false,
  },
  {
    check_id: "footprint.dmarc_missing",
    severity: "info",
    confidence: "certain",
    title: "No DMARC record published",
    detail:
      "The domain publishes no DMARC policy, so receiving mail servers have no instruction for handling mail that fails authentication. This makes the domain easier to spoof.",
    evidence: "_dmarc.taskflow.lovable.app: NXDOMAIN",
    location: "taskflow.lovable.app",
    remediation:
      "Publish a DMARC record starting at p=none to collect reports, then tighten to quarantine or reject once you can see legitimate senders pass.",
    fix: null,
    fix_available: false,
  },
  {
    check_id: "platform.fingerprint",
    severity: "info",
    confidence: "certain",
    title: "Platform fingerprint",
    detail:
      "Identified stack: backend=supabase, builder=lovable, framework=react, host=netlify.",
    evidence: "backend=supabase, builder=lovable, framework=react, host=netlify",
    location: "https://taskflow.lovable.app/",
    remediation: null,
    fix: null,
    fix_available: false,
  },
  {
    check_id: "platform.supabase.rls_untested",
    severity: "info",
    confidence: "certain",
    title: "Supabase detected — Row Level Security not tested by this scan",
    detail:
      "This app talks to Supabase from the browser, so every table in the public schema is reachable by anyone holding the anon key, which ships to every visitor. Whether that is safe depends entirely on RLS policies. A passive scan cannot determine this.",
    evidence: "https://qwertyuiopasdfghjklz.supabase.co",
    location: "https://taskflow.lovable.app/",
    remediation:
      "Verify RLS is enabled on every table and that each has a policy scoping rows to the authenticated user. Enabling RLS without adding a policy denies all access; adding a permissive policy like USING (true) is equivalent to no protection at all.",
    fix: null,
    fix_available: false,
  },
];

export const VULNERABLE_RESULT: ScanResult = {
  url: "https://taskflow.lovable.app",
  score: 13,
  grade: "F",
  counts: { critical: 1, high: 1, medium: 3, low: 1, info: 3 },
  platform: {
    backend: "supabase",
    project_ref: "qwertyuiopasdfghjklz",
    api_url: "https://qwertyuiopasdfghjklz.supabase.co",
    builder: "lovable",
    framework: "react",
    host: "netlify",
  },
  findings: VULNERABLE_FINDINGS,
  assets_scanned: [
    "https://taskflow.lovable.app/",
    "https://taskflow.lovable.app/assets/index-B7xK2p.js",
    "https://taskflow.lovable.app/assets/vendor-9fA1c3.js",
    "https://taskflow.lovable.app/assets/index-B7xK2p.js.map",
  ],
  errors: ["certificate transparency lookup timed out after 5s"],
  duration_seconds: 11.82,
};

export const CLEAN_RESULT: ScanResult = {
  url: "https://myapp.example.com",
  score: 97,
  grade: "A",
  counts: { critical: 0, high: 0, medium: 0, low: 1, info: 2 },
  platform: {
    backend: "supabase",
    project_ref: "zxcvbnmasdfghjklqwer",
    api_url: "https://zxcvbnmasdfghjklqwer.supabase.co",
    framework: "nextjs",
    host: "vercel",
  },
  findings: [
    {
      check_id: "transport.missing_nosniff",
      severity: "low",
      confidence: "certain",
      title: "X-Content-Type-Options header not set",
      detail:
        "Without nosniff, a browser may disregard the declared content type and infer its own, which can turn a file you serve as data into a file it executes as script.",
      evidence: "X-Content-Type-Options: (absent)",
      location: "https://myapp.example.com/",
      remediation: "Send X-Content-Type-Options: nosniff on all responses.",
      fix: null,
      fix_available: false,
    },
    {
      check_id: "platform.fingerprint",
      severity: "info",
      confidence: "certain",
      title: "Platform fingerprint",
      detail: "Identified stack: backend=supabase, framework=nextjs, host=vercel.",
      evidence: "backend=supabase, framework=nextjs, host=vercel",
      location: "https://myapp.example.com/",
      remediation: null,
      fix: null,
      fix_available: false,
    },
    {
      check_id: "platform.supabase.rls_untested",
      severity: "info",
      confidence: "certain",
      title: "Supabase detected — Row Level Security not tested by this scan",
      detail:
        "This app talks to Supabase from the browser, so every table in the public schema is reachable by anyone holding the anon key, which ships to every visitor. Whether that is safe depends entirely on RLS policies. A passive scan cannot determine this.",
      evidence: "https://zxcvbnmasdfghjklqwer.supabase.co",
      location: "https://myapp.example.com/",
      remediation:
        "Verify RLS is enabled on every table and that each has a policy scoping rows to the authenticated user. Enabling RLS without adding a policy denies all access; adding a permissive policy like USING (true) is equivalent to no protection at all.",
      fix: null,
      fix_available: false,
    },
  ],
  assets_scanned: [
    "https://myapp.example.com/",
    "https://myapp.example.com/_next/static/chunks/main-4b2c1a.js",
  ],
  errors: [],
  duration_seconds: 8.31,
};
