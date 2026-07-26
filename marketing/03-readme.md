# Public README (draft)

**This replaces the current root `README.md` when the repo goes public.**

The existing README is a good engineering document but it's structured as internal test
documentation — the testing sections run from line 64 to 138, above the design notes. For a public
repo the README is the landing page and the highest-converting asset you have; the test detail
belongs in `CONTRIBUTING.md`.

What's preserved from the current version: the calibration paragraph, the SSRF design note, the
RLS-gap honesty, and the known limitations. Those are the credibility.

The code rename is done (`01-naming.md` §7), and the repo is pushed to `oversharehq/overshare` —
**private**, deliberately, until the trademark search clears. Before this draft can replace the
root README: the repo goes public, `v1` is tagged (the CI snippet below references it), the PyPI
release is cut, and the acceptable-use policy and `SECURITY.md` exist (`00-strategy.md` §9).

---

```markdown
# Overshare

**Find out what your AI-built app is showing the public — on every deploy.**

Fetches only what your app already serves to any visitor, then reports exposed secrets,
misconfiguration, and forgotten infrastructure. No authentication, no writes, no probing.

Runs on your machine or in CI. Detection is high-confidence only — this scanner is built to be
ignored *less*, not to report more.

[![CI](https://img.shields.io/badge/scan-passing-brightgreen)](#) [![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

---

## Quick start

```bash
pip install overshare
overshare https://myapp.com
```

That's it. No account, no API key, no signup.

```
overshare https://myapp.com

  Score 34  Grade D                     supabase · lovable · next.js

  CRITICAL  Supabase service_role key in bundle    /assets/index-a3f9.js
            Bypasses Row Level Security entirely. Rotate immediately.
  CRITICAL  /.env is publicly readable             /.env
  HIGH      CORS reflects arbitrary origin with credentials
  MEDIUM    Source map published                   /assets/index-a3f9.js.map
  MEDIUM    No Content-Security-Policy

  Not checked: whether RLS is actually enforced. That needs a live read (see below).
```

## In CI

The point of this tool. A scan you run once is a scan you stop running.

```yaml
# .github/workflows/security.yml
name: security
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 3 * * 1'   # catches drift you didn't deploy: expiring certs, DNS
                          # changes, a provider default that moved

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

Findings land in your repository's **Security** tab as code scanning alerts, and GitHub tracks each
one as new, still open, or fixed across runs. The report uploads *before* the job fails, so you
still get the findings on the run that breaks the build.

| Input | Default | Effect |
|---|---|---|
| `url` | *required* | The deployed app to scan |
| `fail-on` | `high` | Lowest severity that fails the job (`never` to report only) |
| `sarif-file` | `overshare.sarif` | Where the SARIF report is written |
| `upload-sarif` | `true` | Publish to code scanning. Set `false` on forks, or private repos without Advanced Security |
| `timeout` | `10` | Per-request timeout, seconds |
| `no-footprint` | `false` | Skip DNS, mail auth and certificate transparency |

Prefer to run it yourself? `pip install overshare && overshare https://myapp.com --fail-on high`
works the same in any CI. Exit codes: `0` clean · `1` findings at or above `--fail-on` · `2` scan
error — a scan that couldn't run fails loudly instead of reporting a falsely clean result.

## What it checks

**Secrets in shipped JavaScript** — Supabase `service_role` (proven by decoding the JWT `role`
claim, not guessed), Stripe live and restricted keys, AWS access key IDs, OpenAI, Anthropic,
GitHub tokens and PATs, Slack, SendGrid, Paddle, Mailgun, Google API keys, private key blocks,
database URIs with passwords, and JWT signing secrets.

**Platform fingerprinting** — Supabase (with project ref), Firebase, Convex, PocketBase; Lovable,
Bolt, v0, Replit, Base44; React, Next.js, Nuxt, SvelteKit, Astro, Vue; Vercel, Netlify,
Cloudflare, Render, Fly, GitHub Pages.

**Transport & config** — CSP presence and `unsafe-*` weakening, HSTS, clickjacking protection,
`nosniff`, `Referrer-Policy`, banner disclosure, cookie flags, CORS origin reflection, TLS
version, certificate validity and expiry, mixed content.

**Exposure** — public source maps, and readable `/.env`, `/.git/HEAD`, `/.git/config`,
`/.aws/credentials`.

**External footprint** — DNS records, SPF (including `+all`), DMARC (including `p=none`), DKIM
selectors, and certificate transparency mining for forgotten staging and admin subdomains that
still resolve.

## Why it flags less than other scanners

Every pattern is anchored on a vendor prefix or an unambiguous structure. **Nothing is flagged on
entropy alone**, because minified bundles are full of build hashes, SRI digests, and UUIDs that
look exactly like secrets.

The tradeoff is deliberate: a scanner that cries wolf gets ignored, and an ignored scanner is
worth nothing. `tests/test_secrets.py::test_benign_bundle_produces_no_findings` feeds in
real-world build hashes, minified identifiers, UUIDs, and a Stripe *publishable* key, and asserts
zero findings. Every new pattern ships with its benign lookalike.

The `service_role` check is the example worth understanding: an anon key and a service_role key
are both JWTs with the same shape. We decode the `role` claim rather than pattern-matching, so we
don't flag the anon key — which is public by design and not a leak.

Our measured false-positive rate is published in [METHODOLOGY.md](METHODOLOGY.md).

## What it does not check

Passive scanning **cannot** tell you whether Supabase Row Level Security is actually enforced.
That requires issuing a real read with the anon key. The report says so explicitly rather than
implying your app is clean — a scanner that stays quiet about its blind spots is worse than no
scanner.

Also not covered: route-level chunks loaded lazily at runtime (needs a headless browser), and
anything behind authentication.

## Is this legal to run?

On your own app, always.

On an app you don't own: the passive checks fetch only what the server already sends to every
visitor — the same requests your browser makes when you visit the page. That's it. There are no
writes, no login attempts, no enumeration, and no use of any credential that wasn't already
public.

**Do not use this to scan apps you don't own and then contact the owner to sell them something.**
Unsolicited "I found a vulnerability, buy my product" is extortion-shaped regardless of intent.
See [ACCEPTABLE_USE.md](ACCEPTABLE_USE.md). Found something real by accident? Disclose it
privately and give them time to fix it.

## Safety

URLs are untrusted input, so the fetcher resolves the hostname, rejects the request if **any**
resolved address is non-public, then connects to the validated IP literal with the original `Host`
and SNI. Pinning the IP is what closes DNS rebinding — without it an attacker returns a public
address for the check and a private one for the connect. Redirects are followed manually so the
same policy applies to every hop.

Blocked: loopback, RFC1918, link-local and cloud metadata (`169.254.169.254`), CGNAT,
IPv4-mapped IPv6, decimal-encoded addresses, `user@host` confusion, and non-HTTP schemes.

## Try it against a broken app

A deliberately vulnerable app is included. Every credential in it is fake.

```bash
python testdata/serve_vulnerable_app.py          # terminal 1
overshare http://127.0.0.1:8000/ --unsafe-allow-private-ips --no-footprint
```

Expect score 0, grade F. Use this to see exactly what the scanner catches — and what it misses —
before you trust it on anything real.

## Options

| Flag | Effect |
|---|---|
| `--json` | Machine-readable output |
| `--output FILE` | Write to a file instead of stdout |
| `--sarif-file FILE` | Write a SARIF 2.1.0 report, for GitHub code scanning or any SARIF viewer |
| `--fail-on LEVEL` | Severity that exits 1: `critical`/`high`/`medium`/`low`/`never` |
| `--show-info` | Include informational findings (platform, DNS, anon key) |
| `--no-footprint` | Skip DNS, mail auth, certificate transparency |
| `--no-ct` | Skip only the CT lookup (crt.sh is slow) |
| `--timeout N` | Per-request timeout in seconds (default 10) |

## Hosted version

Scanning is free and open source, forever — including the Row Level Security check. That isn't a
trial.

[Overshare Cloud](#) is for what the scanner can't do on its own: scan history showing what
regressed between deploys, scheduled monitoring, and a verifiable badge for when a customer asks
for a security review. A higher tier writes the fix against your actual schema and opens it as a
PR.

## Contributing

Detection patterns and platform fingerprints are the most useful contributions. See
[CONTRIBUTING.md](CONTRIBUTING.md) — every new pattern needs a benign lookalike test.

## License

Apache-2.0
```

---

## Notes for implementation

- **Badge in the header must be real or absent.** A fake "passing" badge on a security tool is
  self-immolating.
- **The CI snippet is a broken promise until `v1` is tagged in a public repo.** `uses:
  oversharehq/overshare@v1` is the single most copied line in this README, and it fails with an
  unhelpful resolution error while the repo is private. Tag before you publish, not after.
- **Say that SARIF locates against the scanned URL, not repo files** if anyone asks why alerts are
  repo-level rather than inline PR annotations. That's inherent to scanning a deployed app, and
  explaining it pre-empts a bug report.
- **`METHODOLOGY.md` must exist before launch.** The README links to it and it's the entire
  calibration claim. It cannot 404 — that's the one link HN will click.
- **Move testing detail** from the current README into `CONTRIBUTING.md` verbatim. It's good
  content, wrong audience.
- **The "Is this legal to run?" section is deliberately high in the page.** It's the top comment
  on every post you'll make; answering it before it's asked converts a hostile thread into a
  credible one.
- Add `LICENSE`, `SECURITY.md`, `ACCEPTABLE_USE.md`, and GitHub topics
  (`security`, `security-scanner`, `supabase`, `appsec`, `devsecops`, `sast`, `ci`) before going
  public.
