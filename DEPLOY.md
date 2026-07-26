# Deploying Overshare

Two Fly apps: `overshare-api` (private, no public address) and `overshare-web`
(public, serves `oversharehq.com`). Each has its own `fly.toml` beside its own
Dockerfile, so neither `fly deploy` needs path flags.

First run through on 2026-07-26. What follows now describes a deploy that
happened rather than one inferred from the configs, and the corrections it
needed are recorded in "Things that will bite".

---

## Before the first deploy

You need: a Fly account, `flyctl` installed and logged in, and the domain.

```bash
fly auth login
```

The apps must exist before their configs can deploy into them. `fly apps create`
registers the name without building anything:

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

## Waitlist notifications

Opt-in. With neither variable set, signups are still stored — you just are not
told about them, and `POST /v1/waitlist` behaves identically.

```bash
fly secrets set \
  OVERSHARE_MAILGUN_API_KEY=xxxxxxxx \
  OVERSHARE_MAILGUN_DOMAIN=sandboxXXXX.mailgun.org \
  OVERSHARE_NOTIFY_EMAIL=you@example.com \
  --app overshare-api
```

All three are required. Set only some and nothing is sent — half-configured is
treated as unconfigured on purpose, because Mailgun answers an unknown domain
with a 404 that looks nothing like a credentials problem.

Mail goes out from the Mailgun sending domain, not from `oversharehq.com`. That
is deliberate: the domain's SPF record ends in `-all` and does not list Mailgun,
so sending from it would be dropped silently. To send from your own domain you
must add Mailgun's `include:` to SPF *first*, verify the domain in Mailgun, and
only then set `OVERSHARE_NOTIFY_SENDER`.

**Mailgun sandbox domains only deliver to authorised recipients.** A fresh
account gets `sandboxXXXX.mailgun.org`, and mail to anything else is accepted by
the API and then never arrives. Add your own address under Sending → Domains →
your sandbox → Authorized Recipients, and confirm the verification email, before
concluding this is broken.

If the Mailgun domain was created in the EU region, set
`OVERSHARE_MAILGUN_BASE_URL=https://api.eu.mailgun.net/v3` — the US endpoint
authenticates fine and then 404s on the domain.

The send happens in a background task after the response, and every failure is
swallowed and logged. A provider outage must never turn a stored signup into an
error the visitor sees — they would submit again and conclude it is broken.

To read the list directly:

```bash
fly ssh console --app overshare-api -C "python -c \"
import sqlite3
c = sqlite3.connect('/data/scans.db')
for e, t in c.execute('SELECT email, created_at FROM waitlist ORDER BY created_at DESC'):
    print(t, e)
\""
```

Note the `waitlist` table is deliberately outside the retention sweep, which
only deletes from `scans`.

---

## Domain

```bash
fly certs add oversharehq.com --app overshare-web
fly certs add www.oversharehq.com --app overshare-web
```

`fly certs show` prints the records to add. Both names take the A and AAAA
records Fly gives you — `www` included. Do not point `www` at the apex with a
CNAME: it resolves correctly and still never verifies, because Fly's IPv4 is
shared and its edge only serves a hostname it has independently confirmed.

**`www` also needs a DNS-01 challenge record, and the apex does not.** This cost
an hour on the first run. `force_https = true` makes the edge 301 everything on
port 80, `/.well-known/acme-challenge/` included, so HTTP-01 for a new hostname
bounces to an HTTPS endpoint that has no certificate yet — which is the thing
being issued. Fly's proxy normally intercepts the challenge before redirecting,
but only for hostnames it already knows, so a brand-new `www` cannot bootstrap.
DNS-01 sidesteps HTTP entirely:

```
CNAME  _acme-challenge.www  →  www.oversharehq.com.<app-id>.flydns.net.
```

`fly certs setup www.<domain>` prints the exact target. Issuance followed within
about a minute of that record resolving. Keep the `www` A and AAAA records —
they carry traffic; this one only carries validation.

Symptoms of getting this wrong: `fly certs list` reports `Issued` while
`fly certs check` reports `Not verified`, and TLS fails with a connection reset
rather than a certificate error. Trust `check`, not `list`.

---

## Things that will bite

**The API must bind `::`, not `0.0.0.0`.** This one actually happened. Fly's
private network is IPv6-only, so `overshare-api.internal` resolves to an `fdaa:`
address. An IPv4-only bind listens on a stack nothing on the mesh can reach:
`fly ssh console -C` against `127.0.0.1:8000` returns a healthy `{"status":"ok"}`
while every call through the web proxy 502s with "The scanner is not
responding." The API looks fine from every angle except the one that matters.
`OVERSHARE_HOST = "::"` in `fly.toml` fixes it, and Linux accepts IPv4 on a `::`
socket so nothing is lost. To check which stack is actually listening, `netstat`
is not in the image — read `/proc/net/tcp6` and look for a listener on `1F40`
(port 8000).

**`fly deploy` warns the web app is not listening on `0.0.0.0:3000`.** Ignore
it. The probe runs before Next has finished booting, so the only socket open at
that moment is `hallpass` on 22. The app comes up fine.

**Fly creates two web machines, not one.** `min_machines_running = 1` is a floor,
not a cap, and the deploy adds a second machine for zero-downtime releases. Fine
for the frontend, which is stateless — but it is why the same default must never
be allowed to apply to the API.

**GoDaddy ships records that fight this setup.** The apex carries a managed A
record displayed as "WebsiteBuilder Site" rather than an IP, and it must be
deleted or two thirds of visitors land on a parking page instead of the site —
intermittently, which reads as a flaky deploy rather than a DNS fault. The
pre-existing `www` CNAME to the apex should be *kept*: `www` then follows the
apex automatically, Fly's addresses stay defined in one place, and adding
A/AAAA records for `www` on top of it is rejected anyway, since a CNAME cannot
coexist with other records on the same name.

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
