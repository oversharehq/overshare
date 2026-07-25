# Landing page copy

**For the frontend agent.** `web/app/page.tsx` is currently the unmodified Next.js template — this
is the copy to build against. Replace `LeakScan` / `leakscan` (see `01-naming.md`).

**Structural principle:** this page serves two audiences (`02-messaging.md` §1) who want opposite
things. The developer wants to `pip install`; the founder wants to paste a URL. **Give them
different entry points above the fold rather than compromising on one.** The scan box is the
primary CTA — it's zero-friction and works for both — with the install command immediately beside
it.

Do not build a pricing page until the paid tier exists. An empty pricing page costs more trust
than it earns.

---

## Hero

**H1**
> Know what your app shows the public.

**Sub**
> Open-source security scanner for AI-built web apps. Paste a URL, or run it in CI on every
> deploy. High-confidence detection only — it won't waste your time.

**Primary CTA** — scan input
```
[ https://myapp.com          ] [ Scan free ]
No signup. Results in about 30 seconds.
```

**Secondary CTA** — directly beneath, equal visual weight
```
$ pip install leakscan
$ leakscan https://myapp.com --fail-on high
```
with a copy button and a `View on GitHub →` link.

**Trust strip** (small, under the fold line — text only, no logos we haven't earned)
> Apache-2.0 · No account required · Passive by default · Never scans apps you don't own

---

## Section 2 — What it finds

Three columns. Concrete, no marketing adjectives.

**Secrets in your shipped JavaScript**
> Supabase `service_role` keys that bypass RLS entirely, Stripe live keys, AWS credentials, OpenAI
> and Anthropic tokens, database URIs with passwords. Plus public source maps and readable `/.env`
> and `/.git` paths.

**Misconfiguration**
> Missing or weakened CSP, absent HSTS, clickjacking exposure, cookies without `Secure` or
> `HttpOnly`, CORS that reflects any origin with credentials, outdated TLS, expiring certificates.

**Forgotten infrastructure**
> Certificate transparency logs mined for the staging and admin subdomains you shipped once and
> forgot. Plus SPF, DKIM, and DMARC gaps that let anyone send mail as your domain.

---

## Section 3 — The differentiator

This section is the reason to choose us. Give it real estate.

**H2**
> Every other scanner tells you how many checks it runs. We tell you how often we're wrong.

**Body**
> A security scanner that cries wolf gets ignored, and an ignored scanner is worth nothing.
>
> So nothing here is flagged on entropy. Minified bundles are full of build hashes, SRI digests,
> and UUIDs that look exactly like leaked secrets — every pattern we ship is anchored on a vendor
> prefix or an unambiguous structure instead.
>
> The clearest example: a Supabase anon key and a `service_role` key are both JWTs with the same
> shape. We decode the role claim rather than pattern-matching, so we never flag the anon key —
> which is public by design and not a leak. Most scanners get this wrong.
>
> Our measured false-positive rate is published, with the methodology and the sample set.

**CTA:** `Read the methodology →`

---

## Section 4 — Runs in CI

**H2**
> A scan you run once is a scan you stop running.

**Body**
> Most scanners in this category are a one-time moment: paste a URL, get a score, forget about it.
> Your app changes every deploy. So does its public surface.

Code block:
```yaml
name: security
on: [push]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - run: pip install leakscan
      - run: leakscan https://myapp.com --fail-on high
```

> Exit code 1 on findings at or above your threshold. JSON output for anything else you want to
> do with it.

---

## Section 5 — What it can't do

Keep this. Counter-intuitive but it is the highest-converting section on the page for technical
readers, and it is how a faceless brand earns trust.

**H2**
> What this scanner can't tell you

**Body**
> Passive scanning cannot prove your Row Level Security is actually enforced. That needs a live
> read against your database. The report says so explicitly instead of showing you a green check
> and letting you assume you're fine.
>
> It also can't see route-level code loaded lazily at runtime, or anything behind a login.
>
> We'd rather tell you where the edges are than sell you a number that doesn't mean what you think
> it means.

---

## Section 6 — Legality

**H2**
> Is it OK to scan an app I don't own?

**Body**
> The passive checks fetch only what the server already sends to every visitor — the same requests
> your browser makes when you load the page. No writes, no login attempts, no enumeration, no
> credential that wasn't already public.
>
> Anything deeper requires the owner's written authorisation, and the tool won't do it without.
>
> One thing we ask: **don't scan someone's app and then contact them to sell them something.**
> Unsolicited "I found a vulnerability in your site" is extortion-shaped no matter how good your
> intentions are. If you find something real by accident, tell them privately and give them time.

**CTA:** `Acceptable use policy →`

---

## Section 7 — Open source

**H2**
> You can read every check that produced your score.

**Body**
> This whole scanner is Apache-2.0 on GitHub. There's a deliberately vulnerable test app in the
> repo — run the scanner against it and see exactly what gets caught and what gets missed before
> you trust it on anything real.
>
> Scanning is free forever. That isn't a trial.

**CTA:** `View on GitHub →`

---

## Section 8 — Hosted (soft, until the paid tier ships)

**H2**
> When a customer asks for a security review

**Body**
> Finding problems is the free part. LeakScan Cloud is for what comes next: history that shows
> what regressed between deploys, fixes written against your actual schema rather than generic
> advice, and a verifiable badge you can put in front of a customer who's asking whether you're
> safe to buy from.

**CTA (pre-launch):** `Get notified →` (email capture only — do not fake a checkout)

---

## FAQ

**Do I need an account?**
> No. The free scan needs a URL and nothing else.

**How is this different from the other scanners?**
> It's open source and it runs in CI. Most alternatives are closed, one-shot URL scanners. If a
> scan result is going to change how you ship, you should be able to read the code behind it.

**Lovable already scans my app. Why use this?**
> Lovable's scanners are good, but running them before you publish is optional, and they only ever
> scan Lovable's own output. This works the same on Bolt, Cursor, Replit, v0, or hand-written code
> — and it isn't graded by the same system that wrote the code.

**Is the Supabase anon key a security problem?**
> No — it's public by design and any scanner that flags it as a leak is wrong. It only matters if
> RLS isn't enforced behind it, which is a separate check. The key that must never reach a browser
> is `service_role`, because it bypasses RLS entirely.

**Will you store my scan results?**
> [Answer honestly once brief §12 retention is decided. Do not ship the page with this unresolved.]

**What if it's wrong?**
> Open an issue. False positives are treated as bugs, not noise — a scanner people stop trusting
> is a scanner that failed.

---

## Implementation notes

- **Above the fold must contain a working scan input.** Everything else is secondary.
- **No fake social proof.** No "trusted by 10,000 developers," no invented logos, no fabricated
  testimonials. One provably false trust signal on a security product ends it.
- **No cookie banner theatre, no chat widget, no exit-intent popup.** Wrong audience entirely.
- Show real scanner output in the hero — a terminal render of an actual result, not a stock
  dashboard illustration.
- Page must be fast and work without JS for the content sections. A slow security tool site is an
  argument against itself.
- Placeholder statistics are forbidden. If a number isn't measured yet, omit the sentence.
