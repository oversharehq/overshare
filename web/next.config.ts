import type { NextConfig } from "next";

// Applied to every response. A scanner that ships its own site without these
// fails its own report, and the report is the product.
//
// Content-Security-Policy is deliberately absent. A useful one needs a
// per-request nonce, which in Next means dynamic rendering on every page, and a
// CSP with 'unsafe-inline' instead would trip our own transport.header.csp_weak
// check — trading a finding for a finding while calling it a fix.
const SECURITY_HEADERS = [
  {
    key: "Strict-Transport-Security",
    value: "max-age=31536000; includeSubDomains",
  },
  // Would be redundant with a CSP frame-ancestors directive, which we do not
  // set yet. Until then this is the only clickjacking defence.
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
];

const nextConfig: NextConfig = {
  output: "standalone",

  // Drops `x-powered-by: Next.js`, which our own version-disclosure check flags.
  poweredByHeader: false,

  async headers() {
    return [{ source: "/:path*", headers: SECURITY_HEADERS }];
  },
};

export default nextConfig;
