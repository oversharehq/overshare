# LeakScan — Build Brief

> Security scanner for AI-generated ("vibe-coded") web apps. Free public-surface scan as the funnel; paid authenticated scan + remediation as the product.

**Status:** pre-build. Nothing written yet.
**Owner context:** DevSecOps engineer, building solo, evenings/weekends, day job in Sydney AU.
**Primary goal:** MRR. Secondary: portfolio/career asset.

---

## 1. The product in one paragraph

A user pastes their app's URL. LeakScan fetches only what the app already serves to the public, parses the shipped JavaScript for exposed secrets, fingerprints the backend platform, checks headers/TLS/DNS, and — using the anon key the app already ships to every browser — tests whether Row Level Security is actually enforced. It returns a scored report with severity-ranked findings. Free tier shows what's broken; paid tier shows the correct, app-specific fix and can open a PR. A verifiable badge is issued after a clean re-scan.

---

## 2. Why this market (evidence base)

Keep these figures for landing-page copy and validation conversations. All were publicly reported as of mid-2026 — **re-verify before publishing any of them.**

- **CVE-2025-48757** — RLS misconfiguration in Lovable-built apps. A scan of 1,645 Lovable apps found 170 (~10.3%, 303 endpoints) allowing unauthenticated reads of arbitrary tables: names, emails, financial records, addresses, API keys. Root cause: the AI generated the DB schema but never configured access controls.
- Only **~10.5%** of studied vibe-coded apps were assessed as secure.
- Retool (citing Beesoul data) put roughly **70% of Lovable apps** as having RLS disabled.
- **Stanford (arXiv:2211.03622)** — developers using AI assistants produced vulnerable code ~40% of the time on security-sensitive tasks, *and believed it was more secure than non-AI code.*
- Real incidents: a Lovable exam app with 16 vulnerabilities (6 critical) exposing 18,697 users; a vibe-coded social network leaking 1.5M auth tokens and 35K emails.

**The demand problem to design around:** that Stanford finding is the central obstacle. Users don't believe they have a problem. Sell the *outcome* (a trust artifact that unlocks a sale), not the *fear* (you might get breached).

---

## 3. Competitive position

**Incumbent: vibeappscanner.com (VAS).** Free first scan, 150+ checks, covers Supabase RLS, Firebase rules, API keys in JS bundles, payment secrets, JWT weakness, IDOR, CORS, headers. Per-platform pages for Lovable, Bolt, Cursor, Replit, v0 + 20 more. Already has SEO content built out.

**Platform absorption risk (the serious one).** Lovable ships 4 automated scanners (RLS analysis, DB security check, code review, dependency audit) — but running them pre-publish is *optional*. Bolt has no built-in scan. If Lovable makes scanning mandatory, a chunk of the standalone market evaporates.

### Differentiation — pick these, not "more checks"

1. **Remediation, not detection.** Detection is commoditising and free. The fix — a *correct, app-specific* RLS policy, delivered as a PR — is where the value is and where a generic scanner wrapper can't compete. This is where DevSecOps expertise is the moat: telling a real fix from a plausible-looking wrong one.
2. **The trust artifact.** A verifiable badge + report that answers a customer's security questionnaire or a buyer's due-diligence request. Reframes the purchase from insurance to revenue-enabler.
3. **Cross-platform.** Platforms will only ever scan their own output.

**Do not treat competitors as disqualifying.** Every idea evaluated in this space already had someone in it. One visible player in a fast-growing market is evidence of demand, not a closed door.

---

## 4. Legal boundaries — READ BEFORE WRITING CODE

Non-negotiable. Under **Australia's Criminal Code Act** and the **US CFAA**, unauthorised access to a computer system is the offence. Good intent is not a defence. Getting this wrong ends a cybersecurity career rather than building one.

### Three tiers

| Tier | What it does | Authorisation needed |
|---|---|---|
| **A — Passive** | Fetches only what the app serves to any visitor. Bundle parsing, headers, TLS, DNS, CT logs, Wayback. | None. Safe on any URL. |
| **B — Anon-key read** | Uses the client-side anon key the app *already ships to every browser* to make the same reads any visitor's browser could. This is the RLS check. | None strictly required (key is public by design), but keep disciplined — see below. |
| **C — Authenticated / active** | Owner-supplied credentials, deeper probing, repo access. | **Written owner authorisation, always.** |

### Hard rules

- **Never** point Tier B or C at an app you don't own without the owner's explicit request (they submitted it themselves) or written permission.
- Tier B discipline: single-row read queries only, rate-limited, **no writes**, no enumeration loops, no bulk reads. Prove the door is unlocked; don't walk through it.
- Never attempt logins, never mutate data, never use a key that wasn't already public.
- **Never scan-then-cold-pitch.** Unsolicited "I found a vulnerability, buy my product" reads as extortion regardless of intent, and creates a paper trail showing profit from unauthorised access.
- SSRF protection on the fetcher is mandatory — a malicious submitted URL pointed at internal GCP metadata endpoints is the obvious attack.
- If a real finding on a third-party app surfaces incidentally: responsible disclosure, privately, with time to fix. Nothing public.

---

## 5. Scan check list (v1 scope)

### Tier A — passive (build first)

**JS bundle analysis**
- Supabase `service_role` key in client bundle — *critical, bypasses RLS entirely*
- Stripe / Paddle / LemonSqueezy secret keys
- Generic API key patterns (target ~150 patterns eventually; start with top 20)
- Exposed source maps (unmaps the whole bundle)
- Exposed `.env` / `.git` paths

**Platform fingerprinting** — determines which Tier B checks are relevant
- Supabase / Firebase / Convex / raw Postgres
- Lovable / Bolt / v0 / Replit / Cursor signatures
- Framework + generation

**Transport & config**
- Security headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- TLS version, cert validity, mixed content
- CORS misconfiguration (from response headers only)

**External footprint**
- DNS records; certificate transparency logs → forgotten staging/admin subdomains
- SPF / DKIM / DMARC presence
- Wayback Machine history

### Tier B — anon-key read (build second)

- **RLS enforcement test** — extract anon key from bundle, attempt scoped read against a table that should return nothing, confirm whether unscoped data comes back. *This is the highest-value check in the product.*
- PostgREST / auto-generated API surface discoverable via the anon key's schema access
- Firebase security rules equivalent

### Tier C — authenticated (paid, later)

Owner-supplied credentials. Deeper auth testing, rate-limit checks, dependency CVE scan against a supplied manifest, repo-level secret history scan.

---

## 6. Architecture

```
Intake (URL, optional owner creds)
        ↓
Job queue (async — scans take minutes, not milliseconds)
        ↓
   ┌────┴────┐
Passive    Anon-key
scanner    scanner
   └────┬────┘
        ↓
Findings engine (normalize, severity-score, dedupe across runs)
        ↓
   ┌────┴────┐
Remediation  Report +
generator    badge
   └────┬────┘
        ↓
Postgres + object store (scan history, re-scan to verify fixes)
```

**Design notes**

- **Two scanner lanes as separate worker classes.** Different trust levels, failure modes, rate-limit profiles. Don't merge them.
- **Async by necessity.** A deep scan runs minutes. Never block an HTTP request on it.
- **Worker isolation is not optional.** Workers parse arbitrary JS and hit arbitrary endpoints. Sandbox them: locked-down egress, hard timeouts, memory caps, no access to app secrets.
- **Findings engine dedupes across runs** so re-scans show *deltas* — what got fixed, what regressed.
- **Badge must be verifiable and revocable.** It resolves to a live scan result. A static "passed once" image is worthless and dangerous.
- **Remediation generator = the moat.** LLM input: specific finding + platform fingerprint + schema shape. Output: the actual policy for *that* table, ideally as a PR. Needs a validation harness, not just a good prompt — a plausible-but-wrong RLS policy is the worst possible product failure.

---

## 7. Infrastructure

**Philosophy:** start with the simplest thing that runs, keep the stack portable, migrate to a managed cloud platform when scale or operational overhead justifies it. Don't couple the architecture to a cloud provider before there's traffic.

### v1 stack — start here

| Component | Option | Notes |
|---|---|---|
| API + frontend | **Railway / Render / Fly.io** | All support Docker deploys, zero-to-low cost at low traffic, trivial to migrate from. Pick one, don't overthink it. |
| Scan workers | Same platform, separate service/process | Isolated execution; most platforms support background workers or separate services. |
| Job queue | **SQLite-backed queue (e.g. Oban/BullMQ/pg-boss) or Redis on same platform** | Avoid a separate queue service until queue depth or reliability demands it. |
| Database | **SQLite (single-file) or Postgres add-on** | SQLite is fine for v1. Most platforms offer a managed Postgres add-on (Railway, Render, Fly) when you need it. |
| Secrets | **Platform env vars / secrets UI** | Never in repo. Platform secret injection is sufficient until you need audit logs or rotation. |
| Report storage | **Local disk or S3-compatible bucket** | Backblaze B2 / Cloudflare R2 are cheap and cloud-agnostic. Avoid provider-specific SDKs in app code. |
| CI/CD | **GitHub Actions** | Vendor-neutral; works regardless of where the app runs. |

### Portability rules (keep the migration path open)
- **No provider-specific SDKs in core app code.** Use standard HTTP clients, generic S3 SDKs, standard Postgres drivers. Wrap anything cloud-specific behind a thin adapter.
- **Docker-first.** If it runs in a container locally, it runs anywhere.
- **Secrets via env vars only.** Platform-injectable; no code changes to switch platforms.
- **No proprietary queue or storage primitives.** A job table in Postgres outlasts any managed queue service.

### When to migrate to a cloud platform (GCP, AWS, etc.)
Trigger migration when one of these is true:
- Monthly spend on current platform exceeds ~$50 and a managed platform would be cheaper or more operationally reliable.
- You need features the current platform doesn't provide (VPC isolation, custom egress controls, compliance certifications).
- You have paying users and need SLA guarantees.

GCP is a reasonable target for migration if cloud upskilling becomes a goal — Cloud Run maps cleanly onto the containerised architecture above. But this is an optional future step, not a v1 constraint.

### Own-infrastructure security
Building a security scanner while misconfiguring your own infra is the worst possible look.
- SSRF protection on the fetcher is mandatory — a malicious submitted URL pointed at platform metadata endpoints is the obvious attack.
- No hardcoded secrets, no secrets in env files committed to repo.
- Workers that parse arbitrary JS and hit arbitrary endpoints must have locked-down egress and hard timeouts.
- Private storage only — no public buckets/containers.

### Costs
- Railway/Render/Fly free or hobby tiers: **$0–10/month** at v1 traffic. Upgrade as needed.
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

Findings carry a stable `check_id` so deltas across scans work.

---

## 9. Build sequence

| Milestone | Scope | Est. hours |
|---|---|---|
| **M1 — Passive core** | Bundle fetch + parse, top-20 secret patterns, platform fingerprint, headers/TLS. CLI only, no UI. | 8–12 |
| **M2 — RLS check** | Anon-key extraction, scoped read test, safe rate-limited implementation. | 5–8 |
| **M3 — Free scan product** | Deploy to hosting platform, job queue, minimal UI (paste URL → score), report rendering. | 10–15 |
| **M4 — Calibration** | Run against 20–30 real vibe-coded apps, manually verify every finding, tune false positives. **Cannot be rushed.** | 15–25 |
| **M5 — Paid tier** | Auth, Stripe, remediation generator + validation harness, badge issuance. | 25–40 |

**M1–M4 ≈ 40–60 hours → a launchable free scanner.** Full product 60–100+.

Ship M1–M3 fast, but do not put M4 off — a scanner that produces false negatives is actively harmful, and one bad report destroys trust permanently.

---

## 10. Business model

- **Free:** unlimited Tier A + Tier B scans, findings visible, fixes locked. This is the funnel — no login required, near-zero trust barrier.
- **Paid ($19–39/mo):** full remediation guidance, scan history, re-scan verification, badge.
- **One-off deep scan ($99–199):** authenticated Tier C + report suitable for a buyer or enterprise customer. Anchor against the €500–2,000 manual technical-diligence alternative.

---

## 11. Validation plan (do this in parallel with M1–M3)

**Twenty conversations.** Find people who've shipped a Lovable/Bolt/Replit app. Channels: r/lovable, r/nocode, r/vibecoding, indie-hacker Discords, Show HN comments, X.

**Ask about the sale, not the fear** — the Stanford finding says they'll say "no, I'm fine" to breach questions:
1. Have you ever been asked for a security review by a customer?
2. Did you lose or delay a deal because you couldn't answer security questions?
3. What did you do about security before launching?
4. Have you ever had a security scare? What happened?
5. Would a report you could hand a customer be worth anything to you?

**Also run vibeappscanner's free scan on 3 apps you build yourself.** Learn what it catches, what it misses, and whether its fixes are actually correct. ~2 hours. Do this before writing code.

---

## 12. Open questions / decisions pending

- [ ] **Name availability** — "LeakScan" not verified. Check .com/.dev on a registrar, GitHub + npm collisions, and a basic trademark search before committing. Note: it leans fear-register, which is in tension with the trust-artifact positioning; revisit if the badge angle becomes primary.
- [ ] Free-tier abuse: rate limiting, and does anonymous scanning without signup invite scraping of the service itself?
- [ ] Do we store scan results for apps the submitter may not own? (Retention + privacy policy implications.)
- [ ] Privacy policy + ToS — must honestly describe handling of anon keys and scan results. Liability language for a security product needs care.
- [ ] Badge revocation UX — what happens publicly when an app regresses?
- [ ] Stripe account setup + business registration (owner task, doesn't parallelize with build).

---

## 13. Kill criteria

Revisit the whole project if:
- Lovable and Bolt both make pre-publish scanning mandatory and thorough.
- 20 conversations produce fewer than 5 people who've been asked for a security review by a customer.
- Calibration (M4) shows false-positive rates that can't be brought under control.
