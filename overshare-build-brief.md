# Overshare — Build Brief

> Security scanner for AI-generated ("vibe-coded") web apps. **Open-core:** an OSS CLI and GitHub Action are the wedge; the hosted cloud (history, deltas, validated remediation, badge) is the revenue.

**Status (2026-07-25):** Tier A passive scanner shipped — Python CLI, 159 tests passing. Frontend built against a mock. API layer not started. Tier B not started.
**Owner context:** DevSecOps engineer, building solo, evenings/weekends, day job in Sydney AU.
**Primary goal:** MRR. Secondary: portfolio/career asset.
**Name:** unresolved and blocking — see §12. "Overshare" throughout this document is a placeholder.

> **Document currency.** §2 (evidence) and §4 (legal) are stable. §3 was rewritten 2026-07-25 after competitive re-research invalidated the original — do not restore the old version. §5, §6 and §9 reflect what is actually built. §7 was rewritten when the GCP commitment was dropped.

---

## 1. The product in one paragraph

A developer runs the scanner against their app — from the CLI, in CI, or by pasting a URL. It fetches only what the app already serves to the public, parses the shipped JavaScript for exposed secrets, fingerprints the backend platform, checks headers/TLS/DNS, and — using the anon key the app already ships to every browser — tests whether Row Level Security is actually enforced. It returns a scored report with severity-ranked findings. The detection engine is open source and free forever. The hosted product sells what a one-shot scan can't give you: scan history and deltas, app-specific validated fixes, and a verifiable badge.

---

## 2. Why this market (evidence base)

Keep these figures for landing-page copy and validation conversations. All were publicly reported as of mid-2026 — **re-verify before publishing any of them.**

- **CVE-2025-48757** — RLS misconfiguration in Lovable-built apps. A scan of 1,645 Lovable apps found 170 (~10.3%, 303 endpoints) allowing unauthenticated reads of arbitrary tables: names, emails, financial records, addresses, API keys. Root cause: the AI generated the DB schema but never configured access controls.
- Only **~10.5%** of studied vibe-coded apps were assessed as secure.
- Retool (citing Beesoul data) put roughly **70% of Lovable apps** as having RLS disabled.
- **Stanford (arXiv:2211.03622)** — developers using AI assistants produced vulnerable code ~40% of the time on security-sensitive tasks, *and believed it was more secure than non-AI code.*
- Real incidents: a Lovable exam app with 16 vulnerabilities (6 critical) exposing 18,697 users; a vibe-coded social network leaking 1.5M auth tokens and 35K emails.

**The demand problem to design around:** that Stanford finding is the central obstacle. Users don't believe they have a problem. Sell the *outcome* (a trust artifact, a CI gate that just works), not the *fear* (you might get breached).

---

## 3. Competitive position — rewritten 2026-07-25

**The original version of this section was wrong and has been deleted.** It named one incumbent. There are ~13: vibeappscanner, CheckVibe, SafeToShip, VibeEval, Scanbee, VibeCheck, SupaScan, SupaExplorer, SecureVibing, VibeShip, ChakraView, amihackable.dev, checkmyvibeapp, Aikido.

*(Competitive claims here come from vendor self-description and vendor-authored roundups. Re-verify before betting on any of them.)*

### What is already commoditised

Three of the original differentiators are shipped by competitors today:

- **Free public-surface scan** — SafeToShip offers unlimited, 60-second scans. Its free tier matches §5 Tier A + Tier B feature for feature.
- **Verifiable trust badge** — vibeappscanner ships one.
- **Remediation guidance with code examples** — vibeappscanner ships this too.

Pricing is already compressed: **$9 one-off / $19–59 per month** across the field.

**Implication: the free URL scan is not a funnel, it's table stakes.** Competing on it means an SEO knife fight against 13 players, one of whom already owns the per-platform content.

### Position: open-core

Open-source CLI + GitHub Action as the wedge. Hosted cloud as the revenue. **Open the detection; monetise the fixing, tracking, and proving.**

Why this and not a better free scanner:

1. **CI is a channel none of the 13 occupy.** They all sell one-shot URL scans. A scanner in CI runs on every push — recurring by construction, where a one-shot scan is not.
2. **Open source is what makes a faceless brand credible in security.** The brand is anonymous by choice (§12), so credibility can't come from a founder's face. Published code and published methodology replace it.
3. **Distribution through GitHub and package registries**, not through Google against incumbent SEO.

### The one uncontested differentiator: calibration

Every competitor advertises check counts — "100+ checks", "150+ checks". **None publishes a false-positive rate.**

This is already enforced in code: `tests/test_secrets.py::test_benign_bundle_produces_no_findings` feeds real build hashes, SRI hashes, minified identifiers, UUIDs, and a Stripe *publishable* key into the detector and asserts zero findings. Detection is high-confidence only — vendor-anchored prefixes or structurally provable claims, never entropy heuristics.

Publishing calibration data is the marketing asset and the moat. It is also the hardest thing for a competitor to copy, because it requires being willing to publish an unflattering number.

### Platform absorption risk (still the serious one)

Lovable ships 4 automated scanners (RLS analysis, DB security check, code review, dependency audit) — but running them pre-publish is *optional*. Bolt has no built-in scan. If Lovable makes scanning mandatory and thorough, a chunk of the standalone market evaporates. Open-core hedges this: a CI-integrated cross-platform tool survives a platform fixing its own output.

### Key metric

**Repeat scans per app after 30 days.** If apps scan once and never again, the open-core position failed and this is the 14th one-shot scanner.

---

## 4. Legal boundaries — READ BEFORE WRITING CODE

Non-negotiable. Under **Australia's Criminal Code Act** and the **US CFAA**, unauthorised access to a computer system is the offence. Good intent is not a defence. Getting this wrong ends a cybersecurity career rather than building one.

### Three tiers

| Tier | What it does | Authorisation needed |
|---|---|---|
| **A — Passive** | Fetches only what the app serves to any visitor. Bundle parsing, headers, TLS, DNS, CT logs. | None. Safe on any URL. |
| **B — Anon-key read** | Uses the client-side anon key the app *already ships to every browser* to make the same reads any visitor's browser could. This is the RLS check. | None strictly required (key is public by design), but keep disciplined — see below. |
| **C — Authenticated / active** | Owner-supplied credentials, deeper probing, repo access. | **Written owner authorisation, always.** |

### Hard rules

- **Never** point Tier B or C at an app you don't own without the owner's explicit request (they submitted it themselves) or written permission.
- Tier B discipline: single-row read queries only, rate-limited, **no writes**, no enumeration loops, no bulk reads. Prove the door is unlocked; don't walk through it.
- Never attempt logins, never mutate data, never use a key that wasn't already public.
- **Never scan-then-cold-pitch.** Unsolicited "I found a vulnerability, buy my product" reads as extortion regardless of intent, and creates a paper trail showing profit from unauthorised access.
- SSRF protection on the fetcher is mandatory. **Implemented** — see §6.
- If a real finding on a third-party app surfaces incidentally: responsible disclosure, privately, with time to fix. Nothing public.

### This constrains calibration — M4 splits in two

A consequence that was missed in the original build sequence: **you cannot calibrate Tier B against third-party apps.** The rule above forbids pointing the RLS check at apps you don't own. So:

- **Tier A calibration** — 20–30 real third-party vibe-coded apps. Passive, legal anywhere, can start immediately.
- **Tier B calibration** — requires a corpus of apps **you build yourself** in Lovable/Bolt/v0, with deliberately varied RLS states: no RLS at all, RLS enabled with no policy, a permissive `USING (true)` policy, and a correctly scoped policy. Roughly 8–12 apps.

That self-built corpus is not overhead — it *is* the published calibration data from §3, and building it is the only legal way to know the RLS check works.

### Tier B enforcement should be structural, not conventional

When Tier B is built, encode the discipline (single-row, rate-limited, no writes, no enumeration) as hard constraints in the client itself. Conventions erode under a future refactor; a client that is structurally incapable of issuing a bulk read does not.

---

## 5. Scan check list

### Tier A — passive — **SHIPPED**

**Secrets in shipped JavaScript** — 16 detectors, high-confidence only. Every one is anchored on a vendor-issued prefix or a structurally provable format. Nothing is flagged on entropy.

- Supabase `service_role` — *proven*, not guessed: the key is a JWT, so the payload is decoded and the `role` claim read directly. Critical.
- Supabase `sb_secret_` keys; Supabase anon key classified as **informational**, not a vulnerability (it is public by design).
- Stripe live and restricted keys; Paddle; Mailgun; SendGrid
- AWS access key IDs; GitHub tokens and fine-grained PATs; Slack; OpenAI; Anthropic
- Google API keys (medium — legitimately public for Firebase/Maps, flagged for missing referrer restrictions)
- PEM private key blocks; database URIs containing passwords; JWT signing secrets
- Exposed source maps; readable `/.env`, `/.git/HEAD`, `/.git/config`, `/.aws/credentials`

**Platform fingerprinting** — backend (Supabase with project ref, Firebase, Convex, PocketBase), builder (Lovable, Bolt, v0, Replit, Base44), framework (Next.js, Nuxt, SvelteKit, Astro, React, Vue), host (Vercel, Netlify, Render, Cloudflare, Fly, GitHub Pages). Builder detection matches on URL host label boundaries or injected build artifacts — a marketing page that *mentions* a builder is not a fingerprint.

**Transport & config** — CSP presence and `unsafe-*` weakening, HSTS, clickjacking protection, `nosniff`, `Referrer-Policy`, banner disclosure, cookie flags, CORS origin reflection, TLS version, certificate validity and expiry, mixed content.

**External footprint** — DNS records, SPF (including `+all`), DMARC (including `p=none`), DKIM selectors, and certificate transparency mining for forgotten staging/admin subdomains that still resolve.

*Dropped from original scope:* Wayback Machine history (low signal, slow). *Deliberately not done:* the "~150 patterns" target — pattern count is the metric competitors advertise and it is in direct tension with the calibration differentiator.

### Tier B — anon-key read — **NEXT**

- **RLS enforcement test** — extract anon key from bundle, attempt a scoped read against a table that should return nothing, confirm whether unscoped data comes back. *Highest-value check in the product.* Tier A already emits `platform.supabase.rls_untested` and extracts the `project_ref` as the input to this.
- PostgREST / auto-generated API surface discoverable via the anon key's schema access
- Firebase security rules equivalent

### Tier C — authenticated (paid, later)

Owner-supplied credentials. Deeper auth testing, rate-limit checks, dependency CVE scan against a supplied manifest, repo-level secret history scan.

---

## 6. Architecture

### Repo layout

```
overshare/        Python scanner core + CLI     (shipped)
tests/           159 tests, no network needed  (shipped)
testdata/        deliberately vulnerable app for E2E testing
web/             Next.js frontend, built against a mock
marketing/       GTM plan — start at 00-strategy.md
API_CONTRACT.md  shared contract between web/ and the API layer
```

`overshare/` and `web/` are developed in **separate sessions**, coordinated only through `API_CONTRACT.md`. That file is the source of truth for the JSON shape and says to keep it in sync with `ScanResult.to_dict()`. Check it before changing scanner output.

### Scanner pipeline (as built)

```
URL (untrusted input)
   │
   ▼  fetch/ssrf.py  ── parse → policy → resolve → validate → pin to IP
   ▼  fetch/client.py ── manual redirect loop, re-validates every hop
   ▼  fetch/assets.py ── HTML → script URLs, inline scripts, source maps
   │
   ├──► checks/secrets.py    16 patterns + JWT payload decoding
   ├──► checks/platform.py   backend / builder / framework / host
   ├──► checks/transport.py  headers, cookies, CORS, TLS, exposed paths
   └──► checks/footprint.py  DNS, SPF/DMARC/DKIM, CT-log subdomains
   │
   ▼  findings/model.py ── dedupe → severity sort → score → grade
   │
   ├──► report/terminal.py    human-readable
   └──► ScanResult.to_dict()  JSON — matches API_CONTRACT.md
```

Layering is strict: `fetch/` knows nothing about findings, `checks/` know nothing about HTTP transport (they take strings and dicts), `findings/` knows nothing about either. That's why the whole suite runs in 0.2s with no network.

### Design notes — implemented

- **SSRF defence pins DNS.** Validate-then-request has a TOCTOU hole: an attacker's DNS returns a public IP for the check and a private one for the connect. So the validated **IP literal** is what gets connected to, with `Host` and SNI set to the original name; cert verification still validates against the real hostname. Redirects are followed manually, because automatic following would resolve the next hop and bypass the policy. A host is rejected if **any** resolved address is non-public, not just the one selected.
- **Checks are pure functions over data.** No I/O inside a check. This is what makes the false-positive guard cheap to maintain.
- **Evidence is redacted at construction**, in the detector rather than the renderer, so a raw credential never enters a `Finding` — and therefore cannot reach a log, the JSON, or the future database. Asserted by test.
- **Scoring penalises each check once, not each occurrence.** One leaked key found in three bundles is one thing to fix.
- **A check that didn't run must never read as a check that passed.** Supabase detected but RLS untested emits an explicit finding; a failed CT lookup says "unavailable", not "no subdomains found".

### Design notes — still aspirational

- **Two scanner lanes as separate worker classes.** Different trust levels, failure modes, rate-limit profiles. Don't merge them.
- **Async by necessity.** A deep scan runs minutes. Never block an HTTP request on it.
- **Worker isolation.** Workers hit arbitrary endpoints. Sandbox them: locked-down egress, hard timeouts, memory caps, no access to app secrets.
- **Findings engine dedupes across runs** so re-scans show *deltas*. `check_id` is already stable and designed for this.
- **Badge must be verifiable and revocable.** It resolves to a live scan result. A static "passed once" image is worthless and dangerous.
- **Remediation generator = the paid moat.** LLM input: specific finding + platform fingerprint + schema shape. Output: the actual policy for *that* table, ideally as a PR. Needs a validation harness, not just a good prompt — a plausible-but-wrong RLS policy is the worst possible product failure.

### Known limitations of the shipped scanner

- Only bundles referenced from the initial HTML are fetched. Lazy route chunks are missed; that needs a headless browser, deliberately deferred. `Fetcher` was not abstracted, so adding one is a small real refactor rather than a drop-in.
- Max 25 scripts per page.
- crt.sh throttles aggressively and often fails on a cold query; the scan degrades to an explicit "unavailable" finding.

---

## 7. Infrastructure

**Philosophy:** start with the simplest thing that runs, keep the stack portable, migrate to a managed cloud platform when scale or operational overhead justifies it. Don't couple the architecture to a cloud provider before there's traffic.

**The CLI stays dependency-light** — `httpx` + `dnspython` only. It is the primary distribution channel under open-core, so every added dependency is friction on `pip install` and surface area in a security tool. The hosted API is an opt-in extra (`pip install overshare[api]`).

### v1 stack — start here

| Component | Option | Notes |
|---|---|---|
| API + frontend | **Railway / Render / Fly.io** | All support Docker deploys, zero-to-low cost at low traffic, trivial to migrate from. Pick one, don't overthink it. |
| Scan workers | Same platform, separate service/process | Isolated execution; most platforms support background workers or separate services. |
| Job queue | **Postgres/SQLite job table, or Redis on the same platform** | Avoid a separate queue service until queue depth or reliability demands it. |
| Database | **SQLite (single-file) or Postgres add-on** | SQLite is fine for v1. Managed Postgres add-ons exist on Railway, Render, Fly when needed. |
| Secrets | **Platform env vars / secrets UI** | Never in repo. Sufficient until you need audit logs or rotation. |
| Report storage | **Local disk or S3-compatible bucket** | Backblaze B2 / Cloudflare R2 are cheap and cloud-agnostic. Avoid provider-specific SDKs in app code. |
| CI/CD | **GitHub Actions** | Vendor-neutral; works regardless of where the app runs. Also the distribution channel for the Action itself. |

### Portability rules (keep the migration path open)
- **No provider-specific SDKs in core app code.** Wrap anything cloud-specific behind a thin adapter.
- **Docker-first.** If it runs in a container locally, it runs anywhere.
- **Secrets via env vars only.** No code changes to switch platforms.
- **No proprietary queue or storage primitives.** A job table in Postgres outlasts any managed queue service.

### When to migrate to a cloud platform (GCP, AWS, etc.)
Trigger migration when one of these is true:
- Monthly spend exceeds ~$50 and a managed platform would be cheaper or more operationally reliable.
- You need features the current platform doesn't provide (VPC isolation, custom egress controls, compliance certifications).
- You have paying users and need SLA guarantees.

GCP is a reasonable target if cloud upskilling becomes a goal — Cloud Run maps cleanly onto the containerised architecture above. Optional future step, not a v1 constraint.

### Own-infrastructure security
Building a security scanner while misconfiguring your own infra is the worst possible look.
- SSRF protection on the fetcher is mandatory — implemented, see §6.
- No hardcoded secrets, no committed env files.
- Workers that hit arbitrary endpoints need locked-down egress and hard timeouts.
- Private storage only — no public buckets/containers.

### Costs
- Railway/Render/Fly free or hobby tiers: **$0–10/month** at v1 traffic.
- Backblaze B2 / Cloudflare R2: effectively free until gigabytes of reports.
- **Only variable cost that moves:** LLM calls in the remediation lane — fires only on paid scans. Batch non-urgent ones.

---

## 8. Data model (sketch)

```
users(id, email, created_at, plan)
apps(id, user_id, url, platform_fingerprint, first_seen)
scans(id, app_id, tier, status, started_at, completed_at, score)
findings(id, scan_id, check_id, severity, title, evidence, status)
remediations(id, finding_id, generated_fix, validated, applied_at)
badges(id, app_id, scan_id, issued_at, revoked_at, public_token)
```

Findings carry a stable `check_id` so deltas across scans work. **This is now real** — `check_id` values are shipped and must never be renamed once public; the delta feature and the frontend's anchor links both key off them.

---

## 9. Build sequence

| Milestone | Scope | Est. | Status |
|---|---|---|---|
| **M1 — Passive core** | Bundle fetch + parse, secret patterns, platform fingerprint, headers/TLS, DNS/CT. CLI only. | 8–12h | **Done** — 159 tests |
| **M2 — RLS check (Tier B)** | Anon-key extraction, scoped read test, safe rate-limited implementation with structural constraints. | 5–8h | **Next** |
| **M2.5 — GitHub Action** | `action.yml` + Dockerfile + annotation output. The open-core wedge. | ~3h | Not started |
| **M4a — Tier A calibration** | 20–30 real third-party apps, manually verify every finding. Legal anywhere. | 10–15h | Not started |
| **M4b — Tier B calibration** | 8–12 self-built apps with varied RLS states. **Legally cannot use third-party apps** (§4). | 10–15h | Not started |
| **M3 — Hosted free scan** | API layer, job queue, wire up the existing frontend. | 10–15h | Frontend done, API not started |
| **M5 — Paid tier** | Auth, Stripe, remediation generator + validation harness, badge issuance. | 25–40h | Not started |

**Note the reordering.** M3 was originally third; it is now after calibration. Under the open-core position the hosted free scan is the commoditised layer (§3), and the frontend is unblocked by its mock, so it can wait. The CLI, the Action, and published calibration data are what differentiate.

Do not put calibration off. A scanner that produces false negatives is actively harmful, and one bad report destroys trust permanently — doubly so when the calibration number is the marketing claim.

---

## 10. Business model

**Free forever (open source):** the detection engine, CLI, and GitHub Action. All Tier A + Tier B checks, all findings, generic remediation text. Locking generic advice makes the free tier feel punitive and defends nothing.

**Paid (hosted cloud, $19–39/mo):** scan history and deltas across runs, app-specific *generated and validated* fixes (the `fix` field in the API contract), re-scan verification, badge issuance and revocation, team/multi-app dashboards.

**One-off deep scan ($99–199):** authenticated Tier C + report suitable for a buyer or enterprise customer. Anchor against the €500–2,000 manual technical-diligence alternative.

The line: **detection is free, fixing and proving are paid.** Note the field is already at $9 one-off / $19–59/mo (§3), so there is no room to price above it on features competitors already give away.

---

## 11. Validation plan

**Twenty conversations.** Find people who've shipped a Lovable/Bolt/Replit app. Channels: r/lovable, r/nocode, r/vibecoding, indie-hacker Discords, Show HN comments, X.

**Ask about the sale, not the fear** — the Stanford finding says they'll say "no, I'm fine" to breach questions:
1. Have you ever been asked for a security review by a customer?
2. Did you lose or delay a deal because you couldn't answer security questions?
3. What did you do about security before launching?
4. Have you ever had a security scare? What happened?
5. Would a report you could hand a customer be worth anything to you?

**Add, given the open-core pivot:**
6. Do you run anything in CI on this project today? Would you add a security gate?

**Run competitors' free scans on apps you build yourself.** Now more valuable than before: SafeToShip in particular claims Tier A + B parity, so scan the same self-built corpus from M4b with both and compare findings. That comparison *is* the calibration marketing asset. ~3 hours.

---

## 12. Open questions / decisions pending

- [ ] **Name — BLOCKING.** Gates the GitHub repo, PyPI package, and all marketing copy (currently on `{{NAME}}`/`{{CMD}}` placeholders). Under open-core the package name *is* the brand, and renaming after people have `pip install`ed is painful. "Overshare" is unverified for trademark/domain/PyPI and sits in a saturated `*scan` field. See `marketing/01-naming.md`.
- [ ] `fix` / `fix_available` fields — `API_CONTRACT.md` specifies them on `Finding`; the scanner doesn't emit them yet. `fix_available` encodes which checks earn a paid fix, which is a product decision, not a code one.
- [ ] Free-tier abuse: rate limiting, and does anonymous scanning without signup invite scraping of the service itself?
- [ ] Do we store scan results for apps the submitter may not own? (Retention + privacy policy implications.)
- [ ] Privacy policy + ToS — must honestly describe handling of anon keys and scan results. Liability language for a security product needs care.
- [ ] Badge revocation UX — what happens publicly when an app regresses?
- [ ] Open-source licence choice — needs to permit the open-core split without letting a competitor host the paid features.
- [ ] Stripe account setup + business registration (owner task, doesn't parallelize with build).

---

## 13. Kill criteria

Revisit the whole project if:

- Lovable and Bolt both make pre-publish scanning mandatory and thorough.
- 20 conversations produce fewer than 5 people who've been asked for a security review by a customer.
- Calibration (M4) shows false-positive rates that can't be brought under control. This is now doubly disqualifying: calibration is the *only* uncontested differentiator (§3), so failing it removes the reason to exist.
- **Repeat scans per app after 30 days stays near zero.** That means the CI wedge failed and this is the 14th one-shot scanner in a field already discounting to $9.
- A competitor publishes credible calibration data first and it's better.
