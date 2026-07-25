# Content & SEO

Two things live here: the **data study** (the single highest-leverage asset in this plan) and the
**SEO architecture** (the slow compounding one). Do the study first.

---

# Part 1 — The data study

## Why this is the priority

Every competitor claims their scanner is good. None of them can prove it, because none of them can
show you the code. We can — and the study is how that advantage becomes visible.

It does five jobs at once:

1. Proves the calibration claim with numbers instead of adjectives.
2. Is the only content shape that reliably reaches HN's front page and r/netsec.
3. Doubles as **M4 calibration**, which the brief says cannot be rushed and must happen anyway.
4. Earns the backlinks that make Part 2 work at all.
5. Replaces the founder's face for a faceless brand — research is credible without an author.

**The unmatched hook: it is reproducible.** "Here's the command, here's the tool, run it yourself
and check our numbers." No closed-source competitor can offer that, ever.

## Legal constraints — read before collecting anything

Brief §4 governs. For this study specifically:

- **Tier A only on third-party apps.** Passive HTTP fetches of publicly served content. Nothing else.
- **No Tier B against any app you don't own.** The RLS figures in this study, if any, come only
  from apps you built yourself. State that explicitly in the writeup.
- **Aggregate and anonymised, always.** No app names, no URLs, no domains, no screenshots, no
  "one popular app we found." Nothing that permits re-identification, including unusual finding
  combinations in a small subgroup.
- **No contacting anyone.** Not one owner, not one DM, before or after publication.
- If something severe and identifiable surfaces: private responsible disclosure, time to fix,
  excluded from the writeup.
- Be a good citizen with the crawl: conservative rate limits, honour `robots.txt`, identifiable
  user agent, one pass.

The last point is also positioning — publish the ethics section *inside* the study. "Here's what
we deliberately did not do, and why" is a paragraph none of the 13 could write, and on HN it's the
difference between admiration and a pile-on.

## Method

1. **Sample.** Aim 300–1000 publicly reachable AI-built apps. Source from public showcase
   galleries, certificate transparency for known builder-platform domains, and public directories.
   Document sourcing precisely — it's the first thing that gets questioned.
2. **Scan.** Tier A, single pass, rate-limited, defaults.
3. **Verify by hand.** The critical step and the whole point. Manually confirm a statistically
   meaningful random sample of findings. **Every false positive gets recorded, not quietly
   dropped.**
4. **Publish the FP rate.** Including the ugly parts. A study admitting a 6% false-positive rate on
   one check is infinitely more credible than one implying zero.
5. **Feed fixes back.** Each FP becomes a benign lookalike in `tests/fixtures.py`, per the existing
   contributing rule. Then note in the study that it's fixed.

## What to publish

- Sample size, sourcing method, date range, exact tool version and command
- Distribution of findings by severity and check
- **Measured false-positive rate, per check**
- What the scanner *missed* — seed a known-vulnerable app into the set and report if it was caught
- Explicit limitations: lazy-loaded chunks unscanned, RLS unverifiable passively, single snapshot
- The ethics section
- Reproduction instructions

## Framing

**Title, roughly:** *"We scanned N public AI-built apps. Here's what they leak — and how often we
were wrong."*

The second clause is the whole differentiator. Lead with the methodology, not the scare number.
Publish as research with a product footnote, never as a product post with a research veneer — HN
and r/netsec detect the difference immediately and punish it.

**Do not** re-use brief §2's statistics without re-verifying each one. A security study citing a
stale figure doesn't recover.

## Prerequisite: METHODOLOGY.md

Must exist before launch — the README and landing page both link to it, and it's the one link
skeptical readers will click.

Contents: what each severity level means · why entropy detection is rejected · how `service_role`
is distinguished from anon by decoding the `role` claim · how scoring works (once per check, not
per occurrence) · known blind spots · current measured FP rate · how to report a false positive.

---

# Part 2 — SEO

## Strategy: concede the head, take the long tail

The 13 competitors are in a knife fight over "vibe coding security scanner," "lovable security
scan," and the "best scanner 2026" roundups — several of them *write* those roundups. You will not
win those terms as a solo builder, and trying burns months.

Three places where they aren't:

1. **Problem queries.** People searching the symptom, not the category. Highest intent, barely
   contested, and answering them well demonstrates the expertise that differentiates you.
2. **Developer/CI queries.** The 13 are consumer-URL-scanner shaped. Nobody in this category
   targets CI integration.
3. **The questionnaire moment.** Founder-funnel queries. Genuinely uncontested — the scanners all
   market on fear, not on the sales-unblocking outcome that actually drives purchase.

## Keyword map

**Tier 1 — problem queries (start here)**

| Query cluster | Target page |
|---|---|
| supabase service_role key exposed / in client / leaked | `/checks/supabase-service-role-exposed` |
| is the supabase anon key safe to expose publicly | `/checks/supabase-anon-key` |
| how to check if RLS is enabled / rls not working supabase | `/checks/rls-not-enforced` |
| next.js env variable exposed in client bundle | `/checks/env-var-in-bundle` |
| source map exposed in production / remove source maps | `/checks/source-map-exposed` |
| .env file publicly accessible on my site | `/checks/env-file-readable` |
| stripe secret key in frontend | `/checks/stripe-secret-key` |
| CORS wildcard with credentials | `/checks/cors-reflected-origin` |

**Tier 2 — the questionnaire moment (highest commercial intent)**

- customer asking for a security review, startup, what do I send
- security questionnaire, small SaaS, no SOC 2
- do I need SOC 2 to sell to enterprise
- how to prove my app is secure to a customer
- cheap alternative to a penetration test for a small SaaS

→ target: `/blog/customer-asked-for-a-security-review`. **Write this early.** It maps directly to
the paid tier and no competitor is targeting it.

**Tier 3 — developer/CI**

- security scanner GitHub Action
- scan for secrets in JavaScript bundle
- CI check for exposed API keys
- open source web app security scanner

**Tier 4 — platform pages (contested, do last)**

- is my Lovable app secure / Bolt / Replit / Cursor / v0 app security

Enter this last, and only with genuinely deeper content than the roundups.

## Page architecture

```
/                          landing (04-landing-page.md)
/methodology               calibration + FP rate — prerequisite for everything
/docs                      CLI + GitHub Action docs
/checks/<check-id>         one page per check  ← the main SEO engine
/blog/<slug>               study, questionnaire post, technical writeups
/platforms/<platform>      last priority
/compare/<competitor>      only after you've actually run their scanners
```

### The `/checks/` pages are the engine

One page per check, ~40 pages. Each covers: what it means, why it matters, how to verify it
yourself manually, how to fix it, and when it's *not* actually a problem.

Why this beats normal programmatic SEO:

- Every page is genuinely useful, so it isn't thin content — it's documentation.
- Each maps to a real search query people already type.
- **Every scan report deep-links to them**, so the product itself drives internal traffic and
  earns natural backlinks when people share reports.
- They're the natural landing spot from the study.

The "when it's *not* a problem" section is the differentiator. The anon-key page explaining that
the anon key is public by design and should *not* be flagged will out-rank fear-based competitor
pages, because it's correct and it's what the searcher actually needs.

## Editorial calendar

| Week | Piece | Purpose |
|---|---|---|
| 1–2 | METHODOLOGY.md | Prerequisite. Everything links here |
| 3 | `/checks/` for the top 8 checks | Tier 1 keywords, report deep-links |
| 4 | "Supabase anon key vs service_role: which one actually matters" | Your signature explainer. Highest-value single post |
| 5 | Launch posts | See `07-launch.md` |
| 6 | "Customer asked for a security review — what to send" | Tier 2, maps to paid tier |
| 7–9 | **The data study** | The reputation-defining asset |
| 10 | "Running security scans in CI without drowning in false positives" | Tier 3, developer funnel |
| 11–12 | Remaining `/checks/` pages, platform pages | Long tail |

## Rules

- **Never publish an unverified statistic.** Re-check every figure from brief §2 at time of use.
- **No AI-generated filler.** A security brand caught publishing slop loses the only asset it has.
  Volume is not the strategy here; being right is.
- **Comparison pages only after actually running competitors' scanners** (brief §11 requires this
  anyway). Be scrupulously fair — note where they're genuinely better. Readers trust a comparison
  that concedes something, and the 13 will read every word you write about them.
- **Every claim links to code or method.** That's the entire reason this position works.
