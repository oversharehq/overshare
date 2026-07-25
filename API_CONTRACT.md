# LeakScan API contract (v1)

> **Shared source of truth between the frontend (`web/`) and the API layer (`leakscan/`).**
> The frontend is built against this document and a mock that implements it exactly
> (`web/lib/mock.ts`). If the API needs to diverge, change this file first — both sides
> read it.

**Status:** implemented for M3. API in `leakscan/api/`, client in `web/lib/api.ts`.

- **Base path:** `/v1`
- **Content type:** `application/json` for all requests and responses.
- **Auth:** none in M3. The free scan requires no login by design — it is the zero-friction entry
  point for both audiences.
- **CORS: not needed, and the API should not add it.** The browser never talks to this API
  directly. It calls the frontend's own origin at `/api/v1/*`, and `web/app/api/v1/[...path]`
  proxies to `LEAKSCAN_API_URL` at request time. That keeps every call same-origin and lets the
  API stay unpublished on the internal network (see `docker-compose.yml`).
- **Client IP:** the proxy forwards `X-Forwarded-For` when the platform sets it. The API only
  trusts that header when `LEAKSCAN_TRUST_PROXY=1`, because it is caller-supplied and rate
  limiting depends on it.

---

## 1. Scan lifecycle

```
POST /v1/scans          → 202, scan in `queued`
GET  /v1/scans/{id}      → poll until status is `complete` or `failed`
```

A scan is async because a deep scan runs for minutes (brief §6). The API must never block an
HTTP request on `scanner.scan()`.

### Status values

| Status | Meaning | `result` | Terminal |
|---|---|---|---|
| `queued` | Accepted, not yet picked up by a worker | `null` | no |
| `running` | Worker is executing checks | `null` | no |
| `complete` | Finished. Findings available. | `ScanResult` | yes |
| `failed` | Could not produce a report at all | `null` | yes |

**`complete` does not mean "clean".** A scan with critical findings is `complete`.
`failed` means the scan itself broke — target unreachable, worker timeout, internal error.

Partial failures are **not** `failed`: if the page fetched but the CT-log lookup timed out,
the status is `complete` and the problem appears in `result.errors[]`. This mirrors how
`scanner.scan()` already behaves.

---

## 2. `POST /v1/scans`

### Request

```json
{ "url": "https://myapp.lovable.app" }
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `url` | string | yes | If no scheme is present the API prepends `https://`, matching the CLI's behaviour in `cli.py`. |

### Response — `202 Accepted`

```json
{
  "id": "scn_8f3a1c7e9b204d61",
  "status": "queued",
  "url": "https://myapp.lovable.app",
  "tier": "passive",
  "created_at": "2026-07-25T02:14:03Z",
  "poll_after_ms": 1500
}
```

- `id` — **opaque** string. The frontend never parses it. Format `scn_` + 16–32 URL-safe chars.
- `tier` — `"passive"` (Tier A) in M3. `"anon_read"` (Tier B) once the RLS check ships.
  Reserved: `"authenticated"` (Tier C). See brief §4 — the tier is legally load-bearing, so it
  is explicit in the API rather than implied.
- `poll_after_ms` — how long the client should wait before its first `GET`. Lets the backend
  apply backpressure without a frontend release.

### Cache / dedupe (optional, recommended)

If the same URL completed a scan recently, the API **may** return `200 OK` instead of `202`
with the existing scan object, including its `result`. This bounds cost and stops refresh
loops re-scanning third-party apps. The frontend handles both status codes identically — it
reads `status` and either renders or polls.

---

## 3. `GET /v1/scans/{id}`

### Response — `200 OK`

```json
{
  "id": "scn_8f3a1c7e9b204d61",
  "status": "running",
  "url": "https://myapp.lovable.app",
  "tier": "passive",
  "created_at": "2026-07-25T02:14:03Z",
  "started_at": "2026-07-25T02:14:04Z",
  "completed_at": null,
  "progress": {
    "phase": "scanning_bundles",
    "label": "Reading JavaScript bundles",
    "completed": 4,
    "total": 8
  },
  "result": null,
  "error": null,
  "poll_after_ms": 2000
}
```

`started_at` / `completed_at` are `null` until they happen. `progress` is `null` when
`status` is `queued` or terminal.

### Progress phases

Derived from the real control flow in `scanner.py::_run`. The frontend renders `label`
verbatim, so wording lives in the backend and can change without a frontend release.
`phase` is the stable machine key.

| Order | `phase` | Suggested `label` |
|---|---|---|
| 1 | `resolving` | Checking the target is safe to reach |
| 2 | `fetching_page` | Fetching the page |
| 3 | `parsing_assets` | Finding scripts and assets |
| 4 | `scanning_bundles` | Reading JavaScript bundles |
| 5 | `probing_paths` | Checking for exposed files |
| 6 | `fingerprinting` | Identifying the platform |
| 7 | `footprint` | Checking DNS, mail and certificates |
| 8 | `scoring` | Scoring findings |

`total` may change mid-scan (the bundle count isn't known until phase 3). The frontend
treats progress as indicative, not a guarantee, and never blocks on it reaching `total`.

**Progress is optional, and M3 sends `progress: null`.** `scanner.scan()` is a single blocking
call with nothing to observe from outside, so there is no truthful phase to report. The frontend
falls back to an indeterminate indicator. Reporting real phases means threading a callback
through `scanner.py`; until then, do not fake percentages.

---

## 4. `ScanResult`

Present only when `status` is `complete`. This mirrors `ScanResult.to_dict()` in
`leakscan/findings/model.py` — **keep them in sync**; every field below already exists there
except where noted.

```json
{
  "url": "https://myapp.lovable.app",
  "score": 32,
  "grade": "F",
  "counts": { "critical": 1, "high": 2, "medium": 3, "low": 1, "info": 4 },
  "platform": {
    "backend": "supabase",
    "project_ref": "abcdefghijklmnopqrst",
    "api_url": "https://abcdefghijklmnopqrst.supabase.co",
    "builder": "lovable",
    "framework": "react",
    "host": "netlify"
  },
  "findings": [ /* Finding[] */ ],
  "assets_scanned": ["https://myapp.lovable.app/", "https://.../index-a1b2.js"],
  "errors": ["footprint checks failed: DNS timeout"],
  "duration_seconds": 12.42
}
```

| Field | Type | Notes |
|---|---|---|
| `url` | string | The **final** URL after redirects, not necessarily what was submitted. |
| `score` | integer | 0–100. `100 - Σ severity penalties`, floored at 0. |
| `grade` | string | `A`≥90, `B`≥75, `C`≥60, `D`≥40, else `F`. |
| `counts` | object | All five severity keys always present, zero-valued if none. |
| `platform` | object | All keys optional; `{}` if nothing was fingerprinted. See §5. |
| `findings` | array | Pre-sorted by severity then `check_id`. Frontend does not re-sort by default. |
| `assets_scanned` | string[] | What was actually fetched. Shown in the report as evidence of scope. |
| `errors` | string[] | Non-fatal problems. Rendered as a "partial scan" notice — important for trust: a check that silently didn't run must not read as a check that passed. |
| `duration_seconds` | number | Rounded to 2dp. |

---

## 5. `platform`

Every key is optional. Values come from `leakscan/checks/platform.py`; treat the lists as
open — the frontend renders unknown values as-is rather than falling over.

| Key | Values today |
|---|---|
| `backend` | `supabase` \| `firebase` \| `convex` \| `pocketbase` |
| `builder` | `lovable` \| `bolt` \| `v0` \| `replit` \| `base44` |
| `framework` | `nextjs` \| `nuxt` \| `sveltekit` \| `astro` \| `react` \| `vue` |
| `host` | `vercel` \| `netlify` \| `render` \| `cloudflare` \| `github-pages` \| `fly.io` |
| `project_ref` / `api_url` | Supabase only |
| `project_id` | Firebase only |
| `deployment` | Convex only |

---

## 6. `Finding`

```json
{
  "check_id": "secrets.supabase_service_role",
  "severity": "critical",
  "confidence": "certain",
  "title": "Supabase service_role key exposed in client bundle",
  "detail": "The service_role key bypasses Row Level Security entirely...",
  "evidence": "eyJhbGciO************9k2A",
  "location": "https://myapp.lovable.app/assets/index-a1b2.js",
  "remediation": "Rotate this key immediately in your Supabase dashboard...",
  "fix": null,
  "fix_available": true
}
```

| Field | Type | Notes |
|---|---|---|
| `check_id` | string | **Stable identifier.** Never renamed once shipped — deltas across re-scans key off it (brief §8). Used by the frontend for anchor links and per-check copy. |
| `severity` | enum | `critical` \| `high` \| `medium` \| `low` \| `info` |
| `confidence` | enum | `certain` \| `probable`. The UI labels `probable` findings explicitly — overstating confidence is how a scanner loses trust permanently (brief §9, M4). |
| `title` | string | One line, plain language. |
| `detail` | string | Plain prose, 1–3 sentences. **No markdown** — the frontend renders it as text. |
| `evidence` | string | May be `""`. **Must already be redacted by the backend** via `model.redact()`. See §7. |
| `location` | string \| null | URL or path where it was found. |
| `remediation` | string \| null | *Generic* guidance. **Free tier — always returned.** |
| `fix` | object \| null | *App-specific generated* fix. **Paid tier only.** Always `null` in M3. |
| `fix_available` | boolean | Whether a paid fix could be generated for this finding. Drives the locked upsell teaser. |

### Why `remediation` and `fix` are separate

The brief's differentiator is remediation, not detection (§3.1). But generic advice
("enable HSTS") is commodity — locking it makes the free tier feel punitive and adds no
defensibility. What's worth money is the *app-specific* artifact: the actual RLS policy for
*that* table, ideally as a PR.

So: `remediation` is free, `fix` is paid. The frontend shows `remediation` inline and, when
`fix_available` is true, a locked teaser naming what the paid fix would contain.

`fix` shape is **not finalised** — it lands in M5. Placeholder for planning only:

```json
{ "kind": "sql" | "patch" | "config", "language": "sql", "content": "...", "validated": true }
```

---

## 7. Security requirements on the API layer

These are contract terms, not suggestions. Building a security scanner with a leaky API is
the worst possible look (brief §7).

1. **Never return an unredacted secret.** `evidence` must pass through `model.redact()`
   before it reaches a response, a log, or the database. The frontend displays `evidence`
   verbatim and cannot fix this.
2. **SSRF rejection is a `422`, not a `500`.** `BlockedTarget` from `fetch/ssrf.py` maps to
   `blocked_target` so the frontend can explain *why* rather than showing a generic failure.
3. **Never echo the submitted URL into HTML.** The frontend treats every string in a
   response as untrusted text and never uses `dangerouslySetInnerHTML`. The API should not
   assume otherwise.
4. **Tier B/C require the submitter to assert ownership.** M3 is Tier A only, so this does
   not apply yet, but the `tier` field exists now so the boundary is explicit when it does.

---

## 8. Errors

Any non-2xx returns:

```json
{ "error": { "code": "blocked_target", "message": "Target resolves to a private IP address." } }
```

`message` is shown to the user, so it must be plain language and must not leak internals
(no stack traces, no internal hostnames).

| HTTP | `code` | When | Frontend behaviour |
|---|---|---|---|
| 400 | `invalid_url` | Unparseable, or scheme is not http/https | Inline field error, stay on page |
| 422 | `blocked_target` | SSRF guard rejected it — private IP, loopback, cloud metadata | Explain that only public apps can be scanned |
| 404 | `scan_not_found` | Unknown or expired scan id | "This scan link has expired" + rescan CTA |
| 429 | `rate_limited` | Rate limit hit. **Must** send `Retry-After` (seconds) | Show wait time, disable submit |
| 500 | `internal_error` | Anything unhandled | Generic failure + retry |

A scan that starts and then breaks is **not** an HTTP error — it's `200` with
`status: "failed"` and a populated `error` object using the same shape and codes.

### Rate limiting

Anonymous scanning invites abuse of the service itself (brief §12, open question).
Proposed starting point, to be tuned rather than treated as settled:

- 5 scans per hour per IP
- 1 concurrent running scan per IP
- Requests exceeding either → `429` with `Retry-After`

---

## 9. `GET /v1/health`

```json
{ "status": "ok", "version": "0.1.0" }
```

Used by the container healthcheck and the deploy platform. No auth.

---

## 10. Open questions

Resolved in M3:

- **Cache window** — implemented. `LEAKSCAN_CACHE_SECONDS`, default 300. A repeat scan of the
  same URL inside the window returns `200` with the existing result instead of `202`.
- **Progress** — ships as `null`. See §3.

Still open:

- [ ] **Scan retention.** The store keeps every scan indefinitely, including scans of apps the
      submitter may not own. Nothing expires and nothing is purged. This blocks the "Will you
      store my scan results?" answer on the landing page, and needs a decision plus a
      `DELETE FROM scans WHERE created_at < ?` job before launch.
- [ ] **Worker isolation.** Workers are threads inside the API process. The build brief requires
      sandboxed workers with locked-down egress, because a scan parses arbitrary JavaScript and
      fetches arbitrary URLs. Splitting the worker into its own service is the intended fix.
- [ ] **Tier B.** `tier` accepts `anon_read` in the contract but the API only issues `passive`.
