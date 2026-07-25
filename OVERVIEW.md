# Overshare — how it all fits together

Orientation document. Read this to understand the system as a whole; the other docs go deeper on
their own slice.

| Read this for | File |
|---|---|
| Using the CLI or the GitHub Action, what each check does, how to test it | `README.md` |
| The HTTP contract between frontend and backend | `API_CONTRACT.md` |
| Why we're building this, market, position, launch plan | `marketing/` (start at `00-strategy.md`) |
| The original plan and legal boundaries | `overshare-build-brief.md` |
| Why the product is called Overshare | `marketing/01-naming.md` |

Last updated 2026-07-25.

---

## 1. What it is

Overshare scans the public surface of a web app — mostly apps built with AI tools like Lovable,
Bolt, v0 and Replit — and reports what that app is handing to anyone who visits it. Exposed API
keys in the JavaScript bundle, published source maps, readable `/.env` and `/.git` paths, missing
security headers, weak TLS, permissive CORS, and forgotten subdomains found in certificate
transparency logs.

The name is the thesis: a missing CSP or a published source map isn't a *leak*, but it is
oversharing.

**The commercial position is open-core.** The scanner is the free, open-source wedge, and it is
meant to run in CI on every deploy rather than once. The revenue is the hosted side: scan history
showing what regressed between deploys, fixes written against your actual schema, and a badge you
can show a customer. This matters when reading the code, because it means *the free URL scan is
not the funnel* — it's the commoditised layer. There are roughly a dozen competitors doing exactly
that. See `marketing/00-strategy.md`.

**The one thing that differentiates us is calibration, not coverage.** Competitors advertise check
counts. We intend to publish a false-positive rate. That shapes real decisions in the code — see
§4.

---

## 2. The shape of the system

Three deployable pieces plus a strategy folder.

```
                    ┌───────────────────────────────┐
   browser ────────▶│  web/  (Next.js, port 3000)   │
                    │                               │
                    │  landing page, SEO pages,     │
                    │  scan form, report UI         │
                    │                               │
                    │  /api/v1/[...path]  ──proxy──┐│
                    └───────────────────────────────┘
                                                    │  same-origin, server-side
                                                    ▼
                    ┌───────────────────────────────┐
                    │  overshare/api/  (FastAPI)    │
                    │                               │
                    │  POST /v1/scans   → 202       │
                    │  GET  /v1/scans/{id}          │
                    │  GET  /v1/health              │
                    │                               │
                    │  SQLite job table + workers   │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  overshare/  (scanner core)   │
                    │                               │
                    │  fetch → parse → check → score│
                    └───────────────────────────────┘
                                    │
                                    ▼
                            the target app

   $ overshare https://myapp.com     ← the CLI skips the API entirely
                                       and calls the scanner core directly

   uses: oversharehq/overshare@v1    ← the Action is the CLI in CI: it installs
                                       the scanner, writes SARIF, and uploads it
                                       to GitHub code scanning (action.yml)
```

The CLI, the Action and the web app are three front doors onto the same scanner. The Action is the
one the strategy cares about most — CI is the channel no competitor occupies, and a scan on every
deploy is what makes repeat scans (the key metric) happen at all.

---

## 3. The pieces

### 3.1 Scanner core — `overshare/`

Pure Python, no web framework, two dependencies (`httpx`, `dnspython`). This is what `pip install
overshare` gives you.

| Module | Job |
|---|---|
| `scanner.py` | Orchestrates a scan. Fetch page → parse assets → scan bundles → probe paths → fingerprint → footprint. |
| `fetch/ssrf.py` | The safety layer. Validates and pins a URL to a resolved public IP before anything connects. |
| `fetch/client.py` | `SafeClient` — re-applies the SSRF policy to *every* redirect hop. |
| `fetch/assets.py` | Pulls script URLs and source-map references out of HTML. |
| `checks/secrets.py` | 17 secret patterns, all anchored on vendor prefixes or decodable structure. |
| `checks/transport.py` | Headers, TLS, cookies, CORS, exposed paths. |
| `checks/platform.py` | Fingerprints backend, builder, framework, host. |
| `checks/footprint.py` | DNS, SPF/DKIM/DMARC, certificate transparency. |
| `findings/model.py` | `Finding`, `ScanResult`, severity, scoring, redaction. |
| `report/terminal.py` | Human-readable CLI output. |
| `report/sarif.py` | SARIF 2.1.0, for GitHub code scanning. |
| `cli.py` | Argument parsing, exit codes. |

There are 27 distinct checks. Adding one means adding a `check_id`, which is a **stable
identifier** — it never gets renamed once shipped, because scan-to-scan deltas key off it.

**Scoring.** Each finding carries a severity, and each severity has a penalty: critical 40, high
20, medium 8, low 3, info 0. Score is `100 − total penalty`, floored at zero. Grades are A ≥ 90,
B ≥ 75, C ≥ 60, D ≥ 40, otherwise F.

The subtlety worth knowing: **penalties apply once per `check_id`, not once per occurrence.** One
leaked key found in three different bundles is one problem to fix, not three, and shouldn't tank
the score three times over.

### 3.2 HTTP API — `overshare/api/`

Optional. Installed with `pip install overshare[api]`, so the CLI stays dependency-light.

| Module | Job |
|---|---|
| `app.py` | Routes, validation, rate limiting, settings from environment. |
| `store.py` | SQLite job table. Create, poll, rate-limit counters, cache lookup, orphan reaping. |
| `worker.py` | Thread pool that runs `scanner.scan()` off the request path. |
| `serialize.py` | Converts scanner output into the contract shape, and enforces the free/paid split. |

A scan takes tens of seconds, so it can't happen inside an HTTP request. `POST /v1/scans` returns
`202` with an id immediately; the client polls `GET /v1/scans/{id}` until the status is `complete`
or `failed`.

The job store is a plain table rather than a queue service — deliberately, so it can move to
Postgres by swapping a connection string, and so the deployment platform stays interchangeable.

### 3.3 Frontend — `web/`

Next.js 16 (App Router), TypeScript, Tailwind.

| Route | What it is |
|---|---|
| `/` | Landing page. Scan box and `pip install` side by side. |
| `/p/[platform]` | Statically generated SEO pages — Lovable, Bolt, v0, Replit, Base44, Cursor. |
| `/scan/[id]` | Live report. Polls the API, renders findings. `noindex`. |
| `/api/v1/[...path]` | Server-side proxy to the API. |

Content lives in data files rather than being scattered through components: `lib/platforms.ts`
holds the SEO page copy, `lib/brand.ts` holds the product name, `lib/severity.ts` holds severity
styling.

### 3.4 Strategy — `marketing/`

Not decoration. `04-landing-page.md` is the spec the landing page is built from, and
`01-naming.md` records why the product is named what it is. If you change positioning copy on the
site, change it there first.

---

## 4. Design decisions you'd otherwise have to reverse-engineer

**Detection is precision-first, and that's a product decision, not a technical one.** Nothing is
flagged on entropy. Every secret pattern is anchored on a vendor prefix (`sk_live_`, `AKIA`,
`ghp_`) or decoded to prove the claim. Supabase anon and `service_role` keys are both JWTs with
identical shape, so we decode the role claim rather than pattern-matching — which is why the anon
key is reported as `info` and never as a leak. Minified bundles are full of build hashes and SRI
digests that look exactly like secrets, and one bad report destroys trust permanently. The
consequence is accepted false *negatives*, which is why the report says plainly what it did not
check.

**The browser never talks to the API directly.** It calls the frontend's own origin, and
`web/app/api/v1/[...path]/route.ts` forwards the request server-side. Two reasons: the API needs
no CORS and can stay unpublished on the internal network, and `OVERSHARE_API_URL` stays a
*runtime* variable so one image promotes between environments.

This was originally a `next.config` rewrite, which silently didn't work — rewrites resolve at
build time and bake into the routes manifest, so the backend URL would have to be known when the
image is built. Don't reintroduce that.

**With no backend configured, the frontend serves a mock — and refuses to in production.** Useful
for frontend work without running Python. But a security scanner that quietly returns fabricated
clean results is worse than one that's down, so `lib/mock/guard.ts` returns 503 in a production
build unless explicitly overridden, and a banner marks mock data everywhere else.

**Scans expire after 30 days, and `0` means "keep everything".** A stored scan is a vulnerability
report on a live app, often one the submitter doesn't own, so an unbounded job table is a target
list. The sweep runs hourly on a timer rather than on the request path, because the delete is
unbounded in size and must not sit in front of a user's scan. `OVERSHARE_RETENTION_DAYS=0`
disables purging for self-hosters who want unbounded history — deliberately *not* read as "expire
immediately", since that turns a plausible misconfiguration into data loss. The 30-day window is
also the shape of the paid tier: history and deltas are what Cloud sells.

**SSRF rejection happens before queueing.** `POST /v1/scans` validates the target synchronously so
a blocked address is an immediate `422` rather than a scan that mysteriously fails later. The
error message deliberately doesn't say *why* — the specific reason is a probe result about the
caller's target, on an unauthenticated endpoint.

**Generic remediation is free; the app-specific fix is paid.** Every finding carries `remediation`
(generic guidance, always shown). The `fix` field is the paid artifact and is always `null` until
M5. `serialize.py` marks `fix_available` only where a generated fix would genuinely beat the
generic advice — secrets, RLS policies, CSP, CORS. Offering a paid fix for "add a nosniff header"
would be selling nothing.

---

## 5. Running it

### Everything at once

```bash
docker compose up --build
open http://localhost:3000
```

The API publishes no port; only the web service is reachable.

### Piece by piece, for development

```bash
# Scanner CLI
pip install -e ".[api,dev]"
overshare https://myapp.com --fail-on high

# API
python -m overshare.api                  # port 8000

# Frontend
cd web && OVERSHARE_API_URL=http://127.0.0.1:8000 npm run dev
```

Omit `OVERSHARE_API_URL` and the frontend runs on mock data with a banner saying so.

### Against the bundled vulnerable app

```bash
python testdata/serve_vulnerable_app.py                    # port 8000
overshare http://127.0.0.1:8000/ --unsafe-allow-private-ips --no-footprint
```

**Gotcha:** the test app and the API both default to port 8000. Move one — e.g.
`OVERSHARE_PORT=8001`.

**Second gotcha:** the SSRF guard blocks loopback, so scanning the local test app needs
`--unsafe-allow-private-ips` on the CLI or `OVERSHARE_UNSAFE_ALLOW_PRIVATE_IPS=1` on the API. That
flag disables SSRF protection entirely and logs a warning at startup. Never set it on anything
reachable from the internet.

### Environment variables

| Variable | Default | Notes |
|---|---|---|
| `OVERSHARE_API_URL` | *unset* | Frontend → API. Unset means mock mode. |
| `OVERSHARE_DB_PATH` | `overshare-scans.db` | SQLite job store. |
| `OVERSHARE_HOST` / `OVERSHARE_PORT` | `127.0.0.1` / `8000` | |
| `OVERSHARE_MAX_WORKERS` | `2` | Concurrent scans. |
| `OVERSHARE_SCAN_TIMEOUT` | `10` | Per-request timeout, seconds. |
| `OVERSHARE_RATE_LIMIT_PER_HOUR` | `5` | Per client IP. |
| `OVERSHARE_MAX_CONCURRENT_PER_IP` | `1` | |
| `OVERSHARE_CACHE_SECONDS` | `300` | Repeat scan of same URL returns the cached result. |
| `OVERSHARE_RETENTION_DAYS` | `30` | Scans older than this are deleted hourly. `0` disables purging. |
| `OVERSHARE_TRUST_PROXY` | off | Trust `X-Forwarded-For`. Only behind a proxy you control. |
| `OVERSHARE_UNSAFE_ALLOW_PRIVATE_IPS` | off | Disables SSRF protection. Local testing only. |
| `NEXT_PUBLIC_SITE_URL` | `http://localhost:3000` | **Build-time.** Used by prerendered sitemap/robots/canonicals. |

### Tests

```bash
pytest            # 211 tests
cd web && npx tsc --noEmit && npx eslint . && npm run build
```

---

## 6. Where things stand

| Milestone | State |
|---|---|
| **M1 — passive scanner core** | Done. 27 checks, 17 secret patterns, 211 tests. |
| **M2 — RLS check (Tier B)** | Not started. Reports currently say RLS was *not* tested. |
| **M3 — deploy + UI** | Built, not deployed. API, frontend, Docker and compose all work end to end locally. |
| **CI channel** | Action and SARIF done, unpublished — it needs the `oversharehq` org to be usable. |
| **M4 — calibration** | Not started. This is the differentiator. |
| **M5 — paid tier** | Not started. `fix` field exists in the contract and is always null. |

**Naming** was resolved on 2026-07-25: Overshare, command `overshare`, domain `oversharehq.com`,
GitHub org `oversharehq` (plain `overshare` is taken on GitHub; free on PyPI and npm). The previous
name was dropped over a verified same-category collision, documented in `marketing/01-naming.md`.

**Verified working:** CLI, API, frontend and the proxy between them, all exercised against the
bundled vulnerable app. SSRF rejection, rate limiting, the production mock guard, and the error
taxonomy have all been tested over HTTP.

**Not verified:** nobody has looked at the rendered UI in a browser. It builds, type-checks, lints
and serves correct HTML, but the visual result is unconfirmed.

---

## 7. Open items

### Blocking anything public

**Trademark search.** IP Australia and USPTO TESS, classes 9 and 42. `Oversecured` — an existing
mobile app vulnerability scanner — is the closest risk. This is the only outstanding item that can
force another rename, and a security brand that rebrands mid-flight loses the trust it spent
months building.

**The GitHub org doesn't exist.** Every "View on GitHub" call to action 404s, `pip install
overshare` isn't real yet, and the whole open-core position rests on a repo nobody can read.

### Before real traffic

**Workers aren't isolated.** They run as threads inside the API process. A scan parses arbitrary
JavaScript and fetches arbitrary URLs, so the build brief calls for a separate service with
locked-down egress. Fine locally; not fine exposed.

**Nothing is deployed.** No hosting platform chosen or provisioned.

### Content debt

Five TODO markers are visible on the landing page. They're written so the surrounding sentence
stays true if the marker is deleted — no invented statistics — but they must not ship:

- No measured false-positive rate (needs M4)
- `METHODOLOGY.md` doesn't exist, and three marketing files link to it
- No acceptable use policy page
- No working email capture for the hosted waitlist
- The retention answer is now decided (30 days) but the landing-page TODO still needs the copy,
  and `marketing/03-readme.md` / `04-landing-page.md` still show a raw `pip install` in a
  workflow rather than the Action

Also: `marketing/00-strategy.md §1` competitive claims come from vendor self-description and
vendor-authored roundups. They haven't been independently checked.

---

## 8. Next steps, in order

1. **Trademark search, and buy `oversharehq.com`.** Fifteen minutes. Register PyPI and npm
   `overshare` while you're there — a package name is more painful to lose than a domain.

2. **Publish the repo.** Create the `oversharehq` org, push, cut a PyPI release. Everything in the
   open-core position is downstream of this, and every GitHub link on the site is broken until it
   happens. The Action cannot be used by anyone until the org exists — `oversharehq/overshare@v1`
   is the reference in the README, so publishing also means tagging `v1`.

3. **Write the retention and CI copy.** The purge ships (30 days, hourly); the landing page still
   has a TODO where the honest retention answer goes, and `marketing/03-readme.md` and
   `04-landing-page.md` still show a raw `pip install` in a workflow instead of the Action.

4. **M4 calibration.** 15–25 hours against 20–30 real apps, verifying every finding by hand. Write
   `METHODOLOGY.md` from it and publish the false-positive rate. This is the only uncontested
   differentiator, and it plus the CI channel is what the whole position rests on.

5. **M2 — the RLS check.** The highest-value check in the product; every Supabase report currently
   says it wasn't tested. Deliberately after calibration: adding a new class of detection before
   calibrating the existing ones compounds exactly the failure mode we care most about. It also
   carries the most legal sensitivity — see `overshare-build-brief.md §4`.

6. **Worker isolation, then deploy.**

Running alongside all of it: the twenty validation conversations in the build brief §11, and
running competitors' free scans to correct the strategy doc. Neither needs code.

---

## 9. Rules that are easy to break by accident

- **Never rename a `check_id`.** Scan-to-scan deltas key off it.
- **Never let an unredacted secret reach a response, a log, or the database.** Use
  `findings/model.py::redact`.
- **Never add a detection pattern that isn't provable.** No entropy heuristics. Every new pattern
  needs a benign lookalike added to `BENIGN_BUNDLE` in `tests/fixtures.py`, asserting zero findings.
- **Never run a blanket find-replace over `marketing/`.** One was run during the rename and
  corrupted `01-naming.md`, inverting the section explaining the *rejected* name.
- **Never scan an app you don't own and then contact the owner to sell them something.** It's
  extortion-shaped regardless of intent. `overshare-build-brief.md §4` is the full legal position,
  and it is not optional reading.
