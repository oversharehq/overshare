# Overshare — Tier A (passive scanner)

Fetches only what a web app already serves to any visitor, then reports what it
finds. No authentication, no writes, no probing beyond public content.

See `overshare-build-brief.md` for product context and the legal boundaries that
define what this tool is allowed to do.

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Usage

```bash
.venv/bin/overshare https://example.com
```

| Flag | Effect |
|---|---|
| `--json` | Machine-readable output (this is the format the API will consume) |
| `--output FILE` | Write to a file instead of stdout |
| `--show-info` | Include informational findings (platform fingerprint, DNS, anon key) |
| `--no-footprint` | Skip DNS, mail auth, and certificate transparency |
| `--no-ct` | Skip only the certificate transparency lookup (crt.sh is slow) |
| `--timeout N` | Per-request timeout, seconds (default 10) |
| `--fail-on LEVEL` | Severity that triggers exit code 1: `critical`/`high`/`medium`/`low`/`never` |
| `--unsafe-allow-private-ips` | Disables SSRF protection. Local testing only. |

Exit codes: `0` clean, `1` findings at or above `--fail-on`, `2` scan error.

## What it checks

**Secrets in shipped JavaScript** — Supabase `service_role` (proven by decoding the
JWT `role` claim, not guessed), Stripe live/restricted keys, AWS access key IDs,
OpenAI, Anthropic, GitHub tokens and PATs, Slack, SendGrid, Paddle, Mailgun,
Google API keys, private key blocks, database URIs with passwords, and JWT
signing secrets.

Detection is **high-confidence only**: every pattern is anchored on a vendor
prefix or an unambiguous structure. Nothing is flagged on entropy alone, because
minified bundles are full of build hashes that look exactly like secrets. The
tradeoff is deliberate — a scanner that cries wolf gets ignored.

**Platform fingerprinting** — Supabase (with project ref), Firebase, Convex,
PocketBase; Lovable / Bolt / v0 / Replit / Base44; React, Next.js, Nuxt,
SvelteKit, Astro, Vue; Vercel, Netlify, Cloudflare, Render, Fly, GitHub Pages.

**Transport & config** — CSP (presence and `unsafe-*` weakening), HSTS,
clickjacking protection, `nosniff`, `Referrer-Policy`, banner disclosure, cookie
flags, CORS origin reflection, TLS version, certificate validity and expiry,
mixed content.

**Exposure** — public source maps, and readable `/.env`, `/.git/HEAD`,
`/.git/config`, `/.aws/credentials`.

**External footprint** — DNS records, SPF (including `+all`), DMARC (including
`p=none`), DKIM selectors, and certificate transparency mining for forgotten
staging/admin subdomains that still resolve.

## Testing

### 1. Unit and integration tests

```bash
.venv/bin/python -m pytest -q          # all tests, no network required
.venv/bin/python -m pytest -v tests/test_ssrf.py     # the security boundary
.venv/bin/python -m pytest -v tests/test_secrets.py  # detection + false positives
```

The two that matter most:

- `test_ssrf.py` — every internal-address technique the scanner must refuse:
  loopback, RFC1918, cloud metadata (`169.254.169.254`), IPv4-mapped IPv6,
  CGNAT, decimal-encoded IPs, `user@host` confusion, non-HTTP schemes, and DNS
  entries that mix public and private records.
- `test_secrets.py::test_benign_bundle_produces_no_findings` — the false-positive
  guard. It feeds in real-world build hashes, SRI hashes, minified identifiers,
  UUIDs, and a Stripe *publishable* key, and asserts **zero** findings. When you
  add a pattern, add its benign lookalike here too.

### 2. End-to-end against a local vulnerable app

A deliberately broken app is included. Every credential in it is fake.

```bash
# terminal 1
.venv/bin/python testdata/serve_vulnerable_app.py

# terminal 2
.venv/bin/overshare http://127.0.0.1:8000/ --unsafe-allow-private-ips --no-footprint
```

Expect **score 0, grade F**, and specifically:

| Expected finding | Severity |
|---|---|
| Supabase `service_role` key in bundle | critical |
| Stripe live key (in bundle and in `/.env`) | critical |
| OpenAI, SendGrid, GitHub, AWS keys | critical |
| Database connection string with password | critical |
| `/.env`, `/.git/HEAD`, `/.git/config` readable | critical |
| Public source map | medium |
| Google API key | medium |
| Reflected CORS origin with credentials | high |
| Missing CSP / clickjacking / nosniff / referrer-policy | medium–low |
| Cookie missing `Secure`/`HttpOnly`/`SameSite` | medium |
| Platform: `backend=supabase`, `builder=lovable` | info |

`--unsafe-allow-private-ips` is required because the SSRF guard blocks
`127.0.0.1` by design. Never use that flag on a real target.

### 3. Verify SSRF protection actually holds

These must all be refused:

```bash
.venv/bin/overshare http://169.254.169.254/latest/meta-data/
.venv/bin/overshare http://localhost/
.venv/bin/overshare http://10.0.0.1/
.venv/bin/overshare file:///etc/passwd
```

Each should print a `target rejected` error and exit `2`.

### 4. Sanity-check against real sites

```bash
.venv/bin/overshare https://example.com --show-info
.venv/bin/overshare https://vercel.com --no-ct --json --output /tmp/scan.json
```

A large production site should yield **zero secret findings**. If one appears,
it is almost certainly a false positive — treat it as a bug, add the offending
string to `BENIGN_BUNDLE` in `tests/fixtures.py`, and tighten the pattern.

## Notes on the design

**SSRF defence.** URLs are submitted by untrusted users, so the fetcher resolves
the hostname, rejects the request if *any* resolved address is non-public, then
connects to the validated IP literal with the original `Host` and SNI. Pinning
the IP is what closes DNS rebinding: without it, an attacker can return a public
address for our check and a private one for the connect. Redirects are followed
manually so the same policy applies to every hop.

**Scoring** penalises each check once, not each occurrence — the same leaked key
found in three bundles is one thing to fix.

**Not covered by a passive scan:** whether Supabase RLS is actually *enforced*.
That requires issuing a read with the anon key (Tier B). The scanner explicitly
flags this gap rather than implying the app is safe.

## Known limitations

- Only bundles referenced from the initial HTML are fetched. Route-level chunks
  loaded lazily at runtime are missed; that needs a headless browser.
- crt.sh throttles aggressively and often fails on a cold query. The scan
  degrades gracefully and says so rather than reporting "no subdomains".
- Up to 25 scripts per page are scanned.
