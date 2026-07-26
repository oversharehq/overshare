# Messaging

Source of truth for all copy. Landing page, README, Reddit posts, and launch assets all derive
from this file. Name resolved 2026-07-25 — see `01-naming.md`.

---

## 1. Who we're talking to

### Primary — "the shipping developer"

Uses Cursor, Claude Code, Windsurf, Replit, or writes code with heavy AI assist. Ships to Vercel/
Netlify/Fly. Uses Supabase or Firebase. Technically competent but security is not their day job.
Has a CI pipeline, or could have one in ten minutes.

- **Trigger:** professional hygiene, a red CI check, or a colleague asking "did anyone look at this?"
- **Buys on:** rigour, integration, signal-to-noise.
- **Kills the sale:** false positives. One bad finding and the tool is uninstalled permanently.
- **Reached via:** GitHub, HN, r/webdev, r/devops, r/Supabase, r/cursor.

### Secondary — "the founder at the questionnaire moment"

Built on Lovable or Bolt, possibly non-technical. Has paying users or is close. **A customer just
asked for a security review, a SOC 2 report, or a pentest, and they have nothing to send.**

- **Trigger:** a specific email from a specific customer. Highest-intent moment in this market.
- **Buys on:** unblocking the deal. This is a revenue problem wearing a security costume.
- **Kills the sale:** anything that requires installing a CLI, or a report they can't understand.
- **Reached via:** SEO long-tail, r/SaaS, r/microsaas, r/Entrepreneur, Lovable/Bolt Discords.

### Explicitly not our audience

Security professionals looking for a pentest replacement. Enterprises with compliance programmes.
Anyone wanting a 150-check box-tick. Chasing these dilutes the product and the copy.

---

## 2. Positioning

**One-liner (developer):**
> An open-source security scanner for AI-built apps. Runs in your CI, fails your build on real
> findings, and doesn't cry wolf.

**One-liner (founder):**
> Find out what your app is showing the public — then prove you fixed it.

**Positioning statement (internal, not copy):**
> For developers shipping AI-generated web apps, Overshare is an open-source scanner that reports
> exactly what the app exposes to any visitor. Unlike the closed URL scanners in this category, it
> runs in CI on every deploy and every detection is auditable — because the code is public and the
> false-positive rate is published.

**The wedge sentence — use this everywhere:**
> Every other scanner in this category advertises how many checks it runs. We publish how often
> we're wrong.

---

## 3. Value ladder

Order matters. Lead with 1.

1. **It doesn't waste your time.** High-confidence detection only. Nothing flagged on entropy —
   minified bundles are full of build hashes that look exactly like secrets. A dedicated test
   asserts zero findings on a benign bundle full of realistic lookalikes.
2. **It runs on every deploy.** One `uses:` block in a workflow, `--fail-on high`, exit code 1,
   done. Findings land in your repo's Security tab as code scanning alerts, so GitHub tracks each
   one as new, still open, or fixed across runs — not a one-time scan you forget about the week
   after you run it.
3. **You can read the code.** Every claim is auditable. Reproduce our published results yourself.
4. **It knows what it can't see.** Passive scanning cannot prove RLS is enforced. The report says
   so explicitly instead of implying the app is clean.
5. **It refuses to do the illegal thing.** SSRF-hardened, no writes, no enumeration, no scanning
   apps you don't own.

**Paid adds, in two rungs** (`00-strategy.md` §3):

- **Prove it** (~$19–29/mo) — history and deltas across runs, scheduled monitoring, regression
  alerts, and a verifiable badge you can hand a customer.
- **Remediation** (~$49–99/mo) — validated, app-specific fixes, delivered as a PR.

Tier C authenticated deep scans sell as a one-off ($199–499), not a subscription rung.

---

## 4. Objection handling

Rehearse these. The first two will be the top comment on every post you make.

**"Is this legal? Are you scanning apps without permission?"**
> Passive checks fetch only what the app already serves to every visitor — the same requests your
> browser makes. The RLS check uses the anon key the app itself ships to every browser, issues a
> single scoped read, and never writes or enumerates. It proves the door is unlocked without
> walking through it. Anything beyond that requires the owner's written authorisation. The full
> policy is in the repo.

**"How is this different from [competitor]?"**
> It's open source and it runs in CI. They're closed one-shot URL scanners. If a scan result is
> going to change how you ship, you should be able to read the code that produced it.
Never disparage them. The market having 13 entrants is evidence of demand.

**"Lovable already has built-in scanners."**
> It does, and they're good — but running them before you publish is optional, and they only ever
> scan their own output. If you moved off Lovable, or you're on Bolt or Cursor, or you just want a
> check that isn't graded by the same system that wrote the code, that's this.

**"My app's fine. The AI writes secure code."**
Do not argue. Arguing loses — this is brief §2's central obstacle, and people asked directly say
they're fine. Redirect to the outcome:
> Probably. It takes 30 seconds to have something you can point at when a customer asks.

**"Why should I trust a score from a tool I've never heard of?"**
> You shouldn't, and that's why it's open source. Read the checks. Run it against the deliberately
> vulnerable app in the repo and see exactly what it catches and what it misses.

**"It's open source — why would I ever pay?"**
> You wouldn't, for scanning. Scanning is free forever. You'd pay when you want the fix written
> for your schema, history that outlives the free 30-day window, or a badge to hand a customer.

**"Do you keep my scan results?"**
> For 30 days, then they're deleted automatically. Secrets are redacted before anything is stored,
> and report pages aren't indexed. A stored scan is a list of weaknesses in a live app, so holding
> them forever would just make our database worth attacking. Want us to keep nothing at all? Run the
> CLI — it stores nothing and sends us nothing.

Answer this one plainly and volunteer the reasoning. None of the 13 publish a retention policy, so a
straight number is a cheap trust win — see `00-strategy.md` §3.

**"Won't this be full of false positives?"**
> That's the failure mode the whole design is built around. Detection is anchored on vendor
> prefixes and structure, never entropy. The service_role finding decodes the JWT role claim
> rather than guessing. Our measured false-positive rate is published.

**"The Supabase anon key is public by design — so what?"**
> Correct, and a scanner that flags the anon key as a leak is wrong. It's only a problem if RLS
> isn't enforced behind it, and that's a separate check. What actually matters is the
> `service_role` key, which bypasses RLS entirely and should never reach a browser.

---

## 5. Voice

Security marketing that shouts loses developers. Ours is precise, calm, and slightly
self-limiting — stating what the tool *cannot* do is the strongest available trust signal for a
faceless brand.

**Do:** be specific and technical · name limitations before anyone asks · use real numbers ·
short sentences · let the code carry the authority.

**Don't:** hype ("revolutionary AI-powered") · fear ("hackers are targeting you right now") ·
countdown urgency · check-count bragging · security-theatre emoji · claim credentials the brand
can't verify · disparage competitors.

**Calibration:** the existing README line — *"The tradeoff is deliberate — a scanner that cries
wolf gets ignored"* — is exactly right. More of that.

---

## 6. Reusable boilerplate

**25 words:**
> Open-source security scanner for AI-built web apps. Reports what your app exposes to the public.
> Runs in CI. High-confidence detection only.

**50 words:**
> Overshare is an open-source scanner for AI-generated web apps. It fetches only what your app
> already serves to any visitor — shipped JS, headers, TLS, DNS — and reports exposed secrets and
> misconfiguration. It runs in CI and fails your build on real findings. Detection is
> high-confidence only; the false-positive rate is published.

**Tagline options:**
- Know what your app shows the public. On every deploy.
- The scanner you can read.
- Open-source security scanning for AI-built apps.

**Never write:** "military-grade" · "hackers are waiting" · "100% secure" · "AI-powered security"
· any percentage you have not personally re-verified.
