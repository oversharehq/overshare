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
| `--sarif-file FILE` | *Additionally* write SARIF 2.1.0 to FILE, for GitHub code scanning |
| `--show-info` | Include informational findings (platform fingerprint, DNS, anon key) |
| `--no-footprint` | Skip DNS, mail auth, and certificate transparency |
| `--no-ct` | Skip only the certificate transparency lookup (crt.sh is slow) |
| `--timeout N` | Per-request timeout, seconds (default 10) |
| `--fail-on LEVEL` | Severity that triggers exit code 1: `critical`/`high`/`medium`/`low`/`never` |
| `--unsafe-allow-private-ips` | Disables SSRF protection. Local testing only. |

Exit codes: `0` clean, `1` findings at or above `--fail-on`, `2` scan error.

## Running it in CI

Scanning once tells you about today. The point is to scan every deploy, so a
regression is caught the day it ships rather than the day a customer finds it.

```yaml
name: Security
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 3 * * 1'   # catches drift in things you didn't deploy: expiring
                          # certs, DNS changes, a provider default that moved

permissions:
  contents: read
  security-events: write  # required to publish to the Security tab

jobs:
  overshare:
    runs-on: ubuntu-latest
    steps:
      - uses: oversharehq/overshare@v1
        with:
          url: https://myapp.com
          fail-on: high
```

Findings land in the repository's **Security** tab as code scanning alerts, with
severity, description and remediation, and GitHub tracks each one as new, still
open, or fixed across runs.

| Input | Default | Effect |
|---|---|---|
| `url` | *required* | The deployed app to scan |
| `fail-on` | `high` | Lowest severity that fails the job (`never` to report only) |
| `sarif-file` | `overshare.sarif` | Where the SARIF report is written |
| `upload-sarif` | `true` | Publish to code scanning. Set `false` on forks, or private repos without Advanced Security |
| `timeout` | `10` | Per-request timeout, seconds |
| `no-footprint` | `false` | Skip DNS, mail auth and certificate transparency |
| `python-version` | `3.12` | Python used to run the scanner |

Two behaviours worth knowing. The report is uploaded **before** the job is
failed, so you still get the findings on the run that breaks the build. And a
scan that could not run at all (exit `2`) fails immediately rather than
reporting an empty, falsely clean result.

**Only scan an app you own or have written permission to test.** The Action
takes a URL, and it cannot tell whose it is.

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
- `test_docs_sync.py` — the claims guard. The severity penalties, grade
  thresholds and retention window are stated in three places: this scanner,
  the markdown docs, and the website. It treats the scanner as canonical and
  fails if the others disagree, so **editing `METHODOLOGY.md` or
  `ACCEPTABLE_USE.md` can turn the Python suite red.** It also fails if a
  percentage appears in the false-positive section before it has been measured.

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

Every report ends by restating these. A clean result means the public surface we
know how to check looks right — not that the app is secure. The full account of
what is proven, what is assumed and where the scanner is blind is in
[METHODOLOGY.md](METHODOLOGY.md), including the deliberately empty
false-positive rate.

## Further reading

| Document | What's in it |
|---|---|
| [PRIMER.md](PRIMER.md) | The whole system in prose — follow one scan end to end, and why it's built this way |
| [METHODOLOGY.md](METHODOLOGY.md) | How a finding is proven, what each severity means, known blind spots, how to report a false positive |
| [ACCEPTABLE_USE.md](ACCEPTABLE_USE.md) | Scan what you own or have permission to test. The scan tiers and what each one requires |
| [SECURITY.md](SECURITY.md) | Reporting a vulnerability in Overshare itself |
| [DEPLOY.md](DEPLOY.md) | Running the hosted stack |
| [OVERVIEW.md](OVERVIEW.md) | How the scanner, API, frontend and strategy fit together |
| [web/README.md](web/README.md) | Working on the frontend: the design system, the fixture backend, and how to check a change in a browser |

**Only scan applications you own or have written permission to test.** Good
intent is not a defence under the Australian Criminal Code Act or the US CFAA.
