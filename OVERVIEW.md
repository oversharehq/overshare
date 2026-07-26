# Overshare — how it all fits together

Orientation document. Read this to understand the system as a whole; the other docs go deeper on
their own slice.

| Read this for | File |
|---|---|
| **The whole system explained end to end, in prose** | **`PRIMER.md`** |
| Using the CLI or the GitHub Action, what each check does, how to test it | `README.md` |
| The HTTP contract between frontend and backend | `API_CONTRACT.md` |
| How detection decides what's real, and where it's blind | `METHODOLOGY.md` |
| Getting it onto a server and a domain | `DEPLOY.md` |
| Where the legal line is, for us and for users | `ACCEPTABLE_USE.md` |
| Reporting a vulnerability in Overshare itself | `SECURITY.md` |
| Why we're building this, market, position, launch plan | `marketing/` (start at `00-strategy.md`) |
| The original plan and legal boundaries | `overshare-build-brief.md` |
| Why the product is called Overshare | `marketing/01-naming.md` |

Last updated 2026-07-26 — the day it went live. See §6 for what is real and §8 for what comes next.

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
| `worker.py` | Dispatch threads for bookkeeping; the scan itself runs in a separate process. |
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
| `/methodology` | How detection decides, the severity table, the blind spots, and the deliberately unmeasured false-positive rate. |
| `/acceptable-use` | Scan tiers and what each requires, prohibited uses, retention. |
| `/p/[platform]` | Statically generated SEO pages — Lovable, Bolt, v0, Replit, Base44, Cursor. |
| `/scan/[id]` | Live report. Polls the API, renders findings. `noindex`. |
| `/api/v1/[...path]` | Server-side proxy to the API. |

Content lives in data files rather than being scattered through components: `lib/platforms.ts`
holds the SEO page copy, `lib/brand.ts` holds the product name, `lib/severity.ts` holds severity
styling, and `lib/docs.ts` holds the headings and numbers the two policy pages share with the
root markdown.

**The look is deliberate and it is an argument.** The interface is styled as a technical document,
not a dashboard: warm paper ground, Newsreader serif for prose, IBM Plex Mono for every label and
datum, hairline rules instead of cards, numbered sections, notes floated into the right margin,
and captioned figures. The reasoning is in §4. Design tokens are the `@theme` block in
`app/globals.css`; the layout primitives — `Shell`, `Section`, `Block`, `Note`, `Figure`, `Prose`,
`Code` — are in `components/Paper.tsx`. Build on those rather than reaching for Tailwind's stock
palette. There should be no `slate-*`, `rounded-*` or `shadow-*` anywhere in `web/`.

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

**The frontend is styled as a technical document, and that's positioning rather than taste.** The
only uncontested differentiator is published calibration and stated limits, so the site should look
like something measured and written down — hence paper, serif prose, mono data, hairline rules,
numbered sections, margin notes, captioned figures. Two alternatives were considered and rejected:
all-mono terminal brutalism, and a dark instrument panel with phosphor accents, the latter partly
because it drifts toward the hacker theatre `marketing/02-messaging.md` §5 forbids. The starting
point was stock Tailwind — slate ground, rounded cards, `shadow-sm` — which reads as generic
AI-generated UI and undercuts the argument.

Two consequences worth knowing before you touch CSS. Severity is encoded as **weight plus a rule in
two hues** — vermilion for critical and high, ochre for medium, plain ink for low and info — not as
a five-colour pill scale, because a five-colour scale trains people to read the palette instead of
the finding. And anything global in `globals.css` must live inside `@layer base`: unlayered CSS
outranks Tailwind v4's layered utilities regardless of specificity, so a bare `:focus-visible` rule
silently beats `outline-none` at every call site.

**The two policy pages restate root markdown, and a test stops them drifting.** `/methodology` and
`/acceptable-use` cover the same ground as `METHODOLOGY.md` and `ACCEPTABLE_USE.md`, but the web
image builds from `web/` alone (`docker-compose.yml` sets `context: ./web`) so the pages *cannot*
read those files at build time. Prose is therefore written twice on purpose; every heading and every
load-bearing number is written once, in `web/lib/docs.ts`.

`tests/test_docs_sync.py` treats the scanner as canonical and fails CI if the markdown or the
website disagrees with it on section headings, severity penalties, grade thresholds, or the
retention window. It also fails if a percentage ever appears in the false-positive section before
the calibration run. That test is the reason the duplication is safe — don't delete it and leave
the copies.

**Scans expire after 30 days, and `0` means "keep everything".** A stored scan is a vulnerability
report on a live app, often one the submitter doesn't own, so an unbounded job table is a target
list. The sweep runs hourly on a timer rather than on the request path, because the delete is
unbounded in size and must not sit in front of a user's scan. `OVERSHARE_RETENTION_DAYS=0`
disables purging for self-hosters who want unbounded history — deliberately *not* read as "expire
immediately", since that turns a plausible misconfiguration into data loss. The 30-day window is
also the shape of the paid tier: history and deltas are what Cloud sells.

**Scans run in a separate process, and the split is deliberate.** Dispatch threads keep the
database handle and do the bookkeeping, because that's trusted code. The scan itself is sent to a
process pool, because it parses arbitrary JavaScript from a target we don't control. In-process, a
segfault or a runaway allocation in a parser took the whole API with it. Only data crosses the
boundary — the child gets a URL and returns a dict, and never holds a store handle to write
through. `spawn`, not the platform default: the API process is threaded, and forking a threaded
process copies its locks mid-flight and deadlocks the child. A scan is marked `running` in the
dispatch thread rather than at submit time, because while the pool is saturated the scan really is
still queued.

**Every report ends by saying what it didn't check.** Detection is precision-first, so the errors
this tool makes are *misses* — which means a report that lists findings and stops invites exactly
the wrong reading of a clean result. `report/terminal.py::LIMITATIONS` names the authenticated
surface, RLS, unrecognised key formats, server-side flaws and runtime assembly. Don't delete it to
tidy the output.

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
pytest            # 231 tests
# Build first: PageProps and RouteContext are generated into web/.next/types,
# so type checking a clean checkout before building fails on missing globals.
cd web && npm run build && npx tsc --noEmit && npx eslint .
```

`tests/test_docs_sync.py` is the odd one out: it reads `METHODOLOGY.md`, `ACCEPTABLE_USE.md` and
`web/lib/docs.ts`, and fails if the published severity penalties, grade thresholds or retention
window disagree with the scanner. It runs inside the normal `pytest` job, so there is no separate
CI step to remember — but it does mean **editing those markdown files can break the Python suite**,
which is surprising the first time it happens.

---

## 6. Where things stand

Last updated 2026-07-26, the day it went live.

| Milestone | State |
|---|---|
| **M1 — passive scanner core** | Done. 27 checks, 17 secret patterns, 253 tests. |
| **M2 — RLS check (Tier B)** | Not started. Reports currently say RLS was *not* tested. |
| **M3 — deploy + UI** | Done and live on `oversharehq.com`. |
| **CI channel** | Done and usable. Repo public, `v1` tagged. |
| **Distribution** | Done. `pip install overshare` works — 0.1.0 on PyPI. |
| **M4 — calibration** | **Not started. This is the only thing standing between here and launch.** |
| **M5 — paid tier** | Not started. `fix` in the contract is always null. Waitlist captures demand. |

### What is live

- **`https://oversharehq.com`** and `www.`, valid certificates, on two Fly apps in `syd`. The API
  has no public address, as designed.
- **The site is `noindex`.** `NEXT_PUBLIC_INDEXABLE` is a build arg in `web/fly.toml`, read via
  `web/lib/site.ts`, and it gates the robots meta, the sitemap and the `Sitemap:` line together.
  It compares against the literal `"true"`, so a missing or misspelled value fails closed.
- **`github.com/oversharehq/overshare` is public**, tagged `v1` and `v0.1.0`, CI green on five
  jobs. Private vulnerability reporting is enabled, so `SECURITY.md` points somewhere real.
- **`overshare` 0.1.0 on PyPI**, verified by installing into a clean venv and scanning the live
  site.
- **Waitlist capture** at `POST /v1/waitlist`, with Mailgun notifications from the verified
  subdomain `mg.oversharehq.com`.

### What has actually been verified, not just written

- The full stack end to end **through the production domain**: submit, queue, run, complete.
- **The site scores A (92) against its own scanner.** One finding remains, the missing CSP, and it
  is deliberate — see §7.
- The CLI installed **from PyPI** into a clean environment, scanning the live site.
- `noindex` confirmed in the built output *and* on the live response, in both flag states.
- The waitlist path end to end, including a Mailgun `delivered ... 2.0.0 OK` with no DMARC verdict.
- SSRF rejection, rate limiting, the production mock guard, the error taxonomy, process-isolated
  workers, and SARIF against the official 2.1.0 schema.

### Not verified

- **Safari and Firefox.** Everything visual was checked in Chrome only.
- **The Action's SARIF upload step.** The repo is public now, so this is finally testable; it has
  not been run.
- **Volume restore.** Fly takes daily snapshots and none has ever been restored.

---

## 7. Open items

### The one that matters

**M4 calibration is not started, and everything else is waiting on it.** The site is `noindex`
precisely because the false-positive rate is unmeasured. `METHODOLOGY.md` has a deliberately empty
section, and `tests/test_docs_sync.py` fails the build if a percentage appears there before the
run. This is not a documentation gap — it is the product's only uncontested differentiator, and
until it exists there is a finished product that cannot honestly be advertised.

### Known and accepted

**No Content-Security-Policy on the site.** Every other security header is set. A useful CSP needs
a per-request nonce, and Next can only inject nonces during server-side rendering, so every page
would become dynamically rendered. A CSP carrying `'unsafe-inline'` would trip our own
`transport.header.csp_weak` check — swapping one finding for another and calling it a fix. Reasoning
lives in `web/next.config.ts`. **Do not "resolve" this by adding a weak CSP.**

**No egress control.** Workers run in separate processes, which bounds a crash to one scan, but
that is blast-radius containment and not a sandbox. Fly has no per-app outbound firewall, so the
SSRF guard in `fetch/ssrf.py` is the only thing constraining where a scan can reach. Real egress
control means routing worker traffic through a proxy we run.

**Single-machine by construction.** SQLite on one volume. `fly scale count` above 1 splits the job
table across machines and polls start 404ing. Scaling out means Postgres first; `store.py` was
written for that swap and it has not been done.

**No analytics.** Deliberate — decided 2026-07-26 to wait until the site is indexable, since there
is no traffic to measure. The conversions that matter are already first-party rows in `scans` and
`waitlist`, and the key metric (repeat scans per app after 30 days) can only come from `scans`.

**Trademark: knockout searches only.** USPTO and IP Australia both came back clear on 2026-07-26
(the one prior US `OVERSHARE` mark was abandoned in 2020). That is not a clearance opinion, and the
point to pay an attorney is before a monetised launch.

**Customer-facing email does not exist.** `mg.oversharehq.com` is set up for notifications *to the
operator*. The eventual "Cloud is ready" send to the waitlist is a different problem with different
tooling.

### Content debt

All four `todo` markers are gone from the site. The `Todo` component is kept with no call sites on
purpose: it is the mechanism for flagging copy that outruns its evidence, and the false-positive
rate is the obvious next candidate.

Still outstanding: `marketing/03-readme.md` and `04-landing-page.md` show a raw `pip install` in a
workflow rather than the Action. And `marketing/00-strategy.md §1` competitive claims come from
vendor self-description and vendor-authored roundups; they have not been independently checked.

---

## 8. Next steps

The build is done. **The next unit of work is not a feature.** Resist adding one.

### The default path

1. **M4 calibration.** 15–25 hours against 20–30 real apps, every finding verified by hand, every
   false positive either fixed or the pattern withdrawn. Then fill in the empty section of
   `METHODOLOGY.md` with the rate, the sample and the date. Needs no infrastructure:

   ```bash
   overshare https://someapp.com --json --output runs/someapp.json
   ```

   The brief splits this in two. Tier A calibrates against third-party apps, but **Tier B cannot** —
   the RLS check may not legally be pointed at apps you do not own, so it needs a corpus of 8–12
   apps you build yourself with deliberately varied RLS states. See `overshare-build-brief.md §4`.

2. **Flip `NEXT_PUBLIC_INDEXABLE` to `"true"` and rebuild.** This is the launch. It is one config
   change and it is gated entirely on step 1.

3. **M2 — the RLS check.** The highest-value check in the product; every Supabase report currently
   says it was not tested. Deliberately *after* calibration: adding a new class of detection before
   calibrating the existing ones compounds exactly the failure mode we care most about. Encode the
   Tier B discipline structurally — a client that *cannot* issue a bulk read, rather than one that
   merely does not.

4. **M5 — the paid tier**, once repeat scans show the free tier is being used more than once.

### Decisions worth making deliberately

These are genuine forks, not a checklist. Each trades something real.

**How much calibration is enough before launching?** Twenty to thirty apps is the plan, and it is
15–25 hours. Ten apps would take a weekend and give a number with a wide error bar. The tradeoff is
that a published false-positive rate is a claim you have to defend, and defending it from a sample
of ten is harder than saying nothing. Recommendation: do not shortcut the number that is the entire
differentiator.

**Launch quietly or loudly?** Flipping `INDEXABLE` is a quiet launch — search engines find it
eventually and nothing else happens. A loud launch (Show HN, r/webdev, the vibe-coding communities)
converts far better but spends a one-time card, and spending it before calibration means launching
on the same undifferentiated free-scan pitch as the other thirteen. Recommendation: quiet first,
loud once the rate exists.

**CSP now or later?** Doing it properly means nonces and dynamic rendering on every page. On Fly
there is no CDN in front, so the practical cost is milliseconds rather than a cold start — this is
cheaper than it looks. Against that: it is invisible to users and does not move the launch.
Recommendation: after calibration, before any real traffic.

**RLS check before or after launch?** It is the highest-value check and its absence is stated in
every Supabase report. Building it first makes the product materially better; building it after
means launching with a known hole. But it needs its own calibration corpus, so it is not a small
job. Recommendation: after launch, unless early users say RLS is the reason they will not pay.

**Do the validation conversations happen at all?** The brief calls for twenty. They need no code,
they are the only thing that tests the *pricing*, and they are the easiest item to quietly skip.

### Running alongside all of it

The twenty validation conversations in the build brief §11, and running competitors' free scans to
correct `marketing/00-strategy.md`. Neither needs code, and both change what is worth building.

---

## 9. Rules that are easy to break by accident

- **Never rename a `check_id`.** Scan-to-scan deltas key off it.
- **Never let an unredacted secret reach a response, a log, or the database.** Use
  `findings/model.py::redact`.
- **Never add a detection pattern that isn't provable.** No entropy heuristics. Every new pattern
  needs a benign lookalike added to `BENIGN_BUNDLE` in `tests/fixtures.py`, asserting zero findings.
- **Never run a blanket find-replace over `marketing/`.** One was run during the rename and
  corrupted `01-naming.md`, inverting the section explaining the *rejected* name.
- **Never publish a false-positive rate that hasn't been measured.** The empty section in
  `METHODOLOGY.md` is the point of the document, not an oversight, and `tests/test_docs_sync.py`
  will fail if a percentage appears there.
- **Never change a penalty, grade threshold or the retention default in one place only.** Each of
  those numbers is stated in the scanner, in a root markdown doc, and on the website.
  `tests/test_docs_sync.py` treats the scanner as canonical and fails on the rest; fix the copies
  rather than the test.
- **Never put a bare element or pseudo-class rule in `globals.css` outside `@layer base`.**
  Unlayered CSS beats Tailwind v4's layered utilities at any specificity, so the utility you write
  at the call site silently loses. This already cost a debugging session over a stray focus ring.
- **Never reintroduce stock Tailwind styling in `web/`.** No `slate-*`, no `rounded-*`, no
  `shadow-*`. Use the tokens in `globals.css` and the primitives in `components/Paper.tsx`; the
  reasoning is in §4 and it is a positioning decision, not a preference.
- **Check `ls -lt` before editing `web/` or `marketing/`.** Sessions run concurrently here. On
  2026-07-25 an uncommitted edit to `web/app/page.tsx` was silently overwritten when another
  session rewrote the file. If you must touch a shared file, commit it immediately and verify it
  survived.
- **Never scan an app you don't own and then contact the owner to sell them something.** It's
  extortion-shaped regardless of intent. `overshare-build-brief.md §4` is the full legal position,
  and it is not optional reading.
