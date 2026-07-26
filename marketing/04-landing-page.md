# Landing page copy

**This is the spec of record for `web/`.** The landing page is built from it and the code rename is
done, so this file now leads rather than follows: change positioning copy here first, then in
`web/`. Product is **Overshare**, command `overshare`, site `oversharehq.com` (see `01-naming.md`).

Outstanding content debt on the built page, per `OVERVIEW.md` §7: no measured false-positive rate
(needs M4), `METHODOLOGY.md` doesn't exist yet, no acceptable-use page, and no working email
capture for the hosted waitlist. Each TODO marker is written so the surrounding sentence stays true
if the marker is deleted — keep that property. Nobody has looked at the rendered page in a browser
yet.

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
$ pip install overshare
$ overshare https://myapp.com --fail-on high
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
permissions:
  security-events: write

jobs:
  overshare:
    runs-on: ubuntu-latest
    steps:
      - uses: oversharehq/overshare@v1
        with:
          url: https://myapp.com
          fail-on: high
```

> Findings show up in your repository's Security tab, and GitHub tracks each one as new, still
> open, or fixed across runs. Your build fails on anything at or above your threshold.
>
> Add a weekly `schedule:` trigger and you also catch what you didn't deploy — a certificate about
> to expire, a DNS record that changed, a provider default that moved underneath you.

**Note for the build:** show the four-line `uses:` form, not a `pip install` script. The whole point
of this section is that adoption costs one copied block. The raw CLI belongs in the hero, where the
developer who wants to run it locally is already looking.

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
> Finding problems is the free part — and it stays free, including the Row Level Security check.
>
> Overshare Cloud is for what comes next: history that outlives the free 30-day window and shows
> what regressed between deploys, scheduled re-scans so you hear about it before your customer does,
> and a verifiable badge you can put in front of someone asking whether you're safe to buy from.
>
> When you'd rather not write the fix yourself, a higher tier generates it against your actual
> schema and opens it as a pull request.

**CTA (pre-launch):** `Get notified →` (email capture only — do not fake a checkout)

**Packaging note for whoever builds the pricing page later** (`00-strategy.md` §3): two monthly
tiers — "Prove it" (~$19–29) for history, monitoring and the badge; remediation (~$49–99) for
generated fixes. Authenticated Tier C deep scans are a **one-off** ($199–499), never a
subscription rung. Do not paywall Tier B; the free scan has to beat the incumbents' free scan.

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
> For 30 days, then they're deleted automatically. A stored scan is a list of weaknesses in a live
> app, so keeping it forever would make our database worth attacking — the shortest retention that
> still lets you reload a report and compare two deploys is the right one.
>
> Secrets we find are redacted before anything is written down. Report pages aren't indexed by
> search engines. If you'd rather we kept nothing at all, run the CLI — it stores nothing anywhere
> and never sends your results to us.

**Can I keep longer history?**
> That's the paid tier. 30 days is deliberately enough to see whether your last deploy made things
> worse; keeping months of it, with the diffs between runs and an alert when something regresses, is
> what Overshare Cloud sells.

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

## Visual treatment

Settled 2026-07-25. The page is set as a **technical document, not a SaaS landing page**: warm paper
ground, serif for prose and headlines, mono for every label and datum, hairline rules instead of
cards, numbered sections, asides in a real margin column, and the terminal output presented as a
captioned figure rather than a hero screenshot.

This is downstream of the positioning, not a taste call. The differentiator is published calibration
and stated limits, so the page should read like something measured and written down. Two alternatives
were rejected: all-mono terminal brutalism, and a dark panel with phosphor accents — the latter
because it drifts toward the security theatre §5 of `02-messaging.md` rules out. The previous look
was stock Tailwind, which reads as generic AI-generated UI and quietly argues against a product whose
whole pitch is rigour.

Consequences for anyone writing copy against this spec:

- **Margin notes must be real asides**, drawn from the same approved copy as the body. Don't invent a
  sentence to fill the gutter, and don't split an approved line between the body and the margin. The
  note in the CI section is the existing exit-code sentence; the one in the limits section is the
  existing "we would rather tell you where the edges are" line.
- **Both CTAs now resolve.** "Read the methodology" points at `/methodology`, and the legality
  section points at `/acceptable-use`. Copy for those pages lives in `METHODOLOGY.md` and
  `ACCEPTABLE_USE.md`, not here.
- Section headings, severity penalties, grade thresholds and the retention window are checked against
  the scanner by `tests/test_docs_sync.py`. Positioning copy is free to change; those numbers are
  not.
