# Deploying Overshare

Two Fly apps: `overshare-api` (private, no public address) and `overshare-web`
(public, serves `oversharehq.com`). Each has its own `fly.toml` beside its own
Dockerfile, so neither `fly deploy` needs path flags.

Nothing here has been run yet — this is written from the configs, not from a
deployment that happened. Expect to correct it the first time through.

---

## Before the first deploy

You need: a Fly account, `flyctl` installed and logged in, and the domain.

```bash
fly auth login
```

The apps must exist before their configs can deploy into them. `--no-deploy`
creates them without building anything:

```bash
# from the repository root
fly apps create overshare-api
fly apps create overshare-web
```

The API keeps its job database on a volume. Create it in the same region as the
app or the machine will not schedule:

```bash
fly volumes create overshare_data --size 1 --region syd --app overshare-api
```

---

## Deploy

Order matters once: the web app resolves `overshare-api.internal` at request
time, so deploying it first gives you a site whose scan box 502s until the API
lands.

```bash
# API first — from the repository root
fly deploy

# then the frontend
cd web && fly deploy
```

Check the API came up. It has no public address, so this goes through a machine
rather than over the internet:

```bash
fly ssh console --app overshare-api -C "python -c \"import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/v1/health').read())\""
```

---

## Domain

```bash
fly certs add oversharehq.com --app overshare-web
fly certs add www.oversharehq.com --app overshare-web
```

`fly certs show` prints the records to add at the registrar. Apex needs the A
and AAAA records Fly gives you; `www` is a CNAME to `overshare-web.fly.dev`.
Certificates issue once DNS resolves, usually within minutes.

---

## Things that will bite

**`NEXT_PUBLIC_SITE_URL` is baked at build time.** It is a `[build.args]` entry
in `web/fly.toml`, not an env var. `sitemap.xml`, `robots.txt` and every
canonical URL are prerendered against it. Change it and you must rebuild — and
if you ever deploy the frontend with the default, you publish a live site whose
sitemap advertises `http://localhost:3000`. This fails silently and search
engines index it.

**Never allocate a public IP on `overshare-api`.** The whole design is that the
scan API has no public surface, needs no CORS, and cannot be hit directly to
bypass the frontend's rate limiting. `fly ips list --app overshare-api` should
stay empty of public addresses.

**Never `fly scale count` the API above 1.** It keeps state in SQLite on a
single volume. A second machine gets a second volume and its own half of the
scans, so a poll for a scan id lands on the wrong machine and 404s. Scaling out
means moving to Postgres first — `store.py` was written for that swap, but it
has not been done.

**`OVERSHARE_TRUST_PROXY=1` is only safe while the API stays private.** It makes
the API believe `X-Forwarded-For`, which is what lets rate limits apply per
visitor rather than lumping every user into one bucket. The moment the API is
publicly reachable, that header is caller-controlled and the rate limit becomes
decorative.

---

## What this does *not* give you

**Egress filtering.** I said earlier this could be expressed in `fly.toml`; it
cannot. Fly has no per-app outbound firewall. A scan makes requests to arbitrary
attacker-influenced URLs, and the controls against that are the SSRF guard in
`fetch/ssrf.py` — which validates and pins to a resolved public IP on every
redirect hop — plus the process boundary added in `api/worker.py`. Those bound
what a scan can *reach* and what it can *damage*, but nothing at the network
layer stops a worker making an outbound connection. Real egress control means
routing worker traffic through a proxy you control, and that is not built.

**Worker sandboxing beyond process isolation.** Scans run as separate processes,
so a crashed or leaking parser takes down one scan instead of the API. They are
not sandboxed: same filesystem, same network namespace, same credentials.

**Backups.** Fly volumes snapshot daily by default, but nothing here has been
verified end to end, and no restore has ever been tested. Given scans expire
after 30 days, the job table is closer to a cache than a system of record — but
that is an argument for deciding deliberately, not for assuming.

---

## Rolling back

```bash
fly releases --app overshare-web
fly releases rollback <version> --app overshare-web
```

The API rolls back the same way, but note that a rollback does not touch the
volume, so a schema change would need handling separately. `store.py` only ever
issues `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`, so rolling
back the current schema is safe.
