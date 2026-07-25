# Marketing strategy

**Date:** 2026-07-25 · **Status:** v1, written pre-launch · **Owner:** solo, evenings/weekends

Read this first. Every other file in `marketing/` is downstream of the decisions here.

---

## 1. Market reality (this supersedes brief §3)

The build brief describes a market with one visible incumbent. That is no longer true.

Products active in "security scanner for AI-built apps" as of July 2026:

vibeappscanner · CheckVibe · SafeToShip · VibeEval · Scanbee · VibeCheck · SupaScan ·
SupaExplorer · SecureVibing · VibeShip · ChakraView · amihackable.dev · checkmyvibeapp · Aikido

### What is already commoditised

| Thing the brief treated as a differentiator | Current market state |
|---|---|
| Free public-surface scan as funnel | SafeToShip: unlimited free scans, 60 seconds. CheckVibe: free tier. Table stakes. |
| The Tier A check list | SafeToShip ships headers, TLS, exposed files, JS secrets, RLS, Firebase rules, CORS, cookie flags, SPF/DKIM/DMARC, stack detection. That is our §5 scope, feature for feature. |
| Verifiable trust badge | vibeappscanner already issues one on a clean scan. |
| Remediation guidance | vibeappscanner ships per-finding risk, evidence, step-by-step fixes with code, plus markdown export to paste into Claude/ChatGPT. |
| The brief's original single $19–39/mo tier | SafeToShip $9 one-off / $24/mo · CheckVibe free + $24–59/mo · VibeEval $19/mo or $199 lifetime. Superseded — see the packaging table in §3. |

**Sourcing caveat:** most of the above comes from vendor self-description and "best scanner"
roundups that competing vendors themselves author. Treat as directionally reliable, not verified.
Brief §11 already calls for running competitor scans against your own apps — do it, and correct
this table.

### What is not commoditised

1. **Being right.** Every competitor advertises check *counts* (100+, 150+). None publishes a
   false-positive rate or a methodology you can audit. The one comparison article in this space
   frames differentiation on "calibration discipline" — nobody is claiming that ground.
2. **Running continuously.** All 13 are paste-a-URL, one-shot, consumer-moment products. One
   competitor is explicitly criticised for charging per scan with no continuous monitoring.
3. **Being verifiable.** They are all closed boxes asking you to trust a scan score from an
   anonymous vendor.

---

## 2. Position

> **Open-source scanner. Paid cloud.**

The scanner is free, auditable, and runs in your CI. The hosted product sells what open source
cannot: history, validated fixes, and proof you can hand a customer.

This is not a hedge. It is picked because all three defensible assets above are things we can
actually hold, and two of them are **already in the code**:

- `--fail-on` + exit codes `0/1/2` and `--json` → CI-native today. The competition cannot follow
  without rebuilding as a dev tool.
- "Detection is high-confidence only… nothing is flagged on entropy alone… a scanner that cries
  wolf gets ignored," backed by `test_benign_bundle_produces_no_findings` → the calibration claim
  is enforced by a test, not a marketing sentence.
- SSRF defence with DNS-rebinding protection and IP pinning → the rigour is inspectable.

### Why this beats fighting on their turf

| | The 13 | Us |
|---|---|---|
| Discovery | SEO knife fight on "lovable security scanner" | GitHub, HN, CI marketplaces, package registries |
| Buyer | Non-technical founder, one-time panic | Developer, recurring in pipeline |
| Retention | Scan once, leave | Runs on every deploy |
| Credibility | "Trust our score" | "Read the code, reproduce the study" |
| Faceless brand | Handicap | Normal — OSS projects are org-branded by default |

That last row matters. The chosen brand posture is faceless, which is a real disadvantage for a
security product where buyers ask "who are you to tell me my RLS is wrong?" **Open source is the
answer to that question.** Code is the credential. Show your work instead of your CV.

---

## 3. The open/closed boundary

Decide this once and do not drift. Open-sourcing is irreversible.

**Open (MIT or Apache-2.0):**
all Tier A detection, the Tier B RLS check, CLI, GitHub Action, JSON schema, SSRF fetcher,
the vulnerable test app, scoring logic, and the methodology docs.

**Closed (the product):**
hosted scans + queue · scan history and cross-run deltas · **validated remediation generation** ·
badge issuance and verification · multi-app and team views · scheduled monitoring and alerts.

**The rule:** open source the *detecting*. Monetise the *fixing, the tracking, and the proving*.

This is brief §3 differentiator #1 taken to its conclusion — detection is commoditising and free,
so stop pretending it is an asset and convert it into distribution instead.

### Packaging

Ordered by what recurs and what is cheap to build — **not** by scan depth.

| Tier | Contents | Why it sits here |
|---|---|---|
| **Free** (OSS + hosted) | Tier A **and Tier B**, all findings, generic remediation, CLI, GitHub Action | Must be at least as good as SafeToShip's free tier or the funnel dies |
| **~$19–29/mo — "Prove it"** | Scan history and cross-run deltas, scheduled monitoring, regression alerts, **verifiable badge**, shareable report | Cheap to build (storage + cron + a public page), high margin, recurring, and it sells at the questionnaire moment |
| **~$49–99/mo — Remediation** | Validated app-specific fixes, PR generation | The moat, and where LLM cost lives — so it prices higher |
| **$199–499 one-off** | Tier C authenticated deep scan + report | Anchor against the €500–2,000 manual technical-diligence alternative |

Three decisions worth not re-litigating later:

- **Tier B must be free.** The RLS enforcement check is the highest-value check in the product, and
  SafeToShip already probes Supabase RLS in *its* free tier. Paywalling ours makes our free scan
  worse than the incumbent's, which kills the wedge.
- **Tier C is a one-off, not a subscription rung.** People buy it when a specific deal demands it,
  then don't need it again for months. It is also the most expensive thing to build and the
  heaviest legally — a bad choice for an entry paid tier.
- **Remediation is not the top of a depth ladder.** It is the upsell from *any* finding, at the
  moment someone sees something red. Making a user upgrade twice — once to scan deeper, once to
  fix — adds friction exactly where intent peaks.

The two monthly tiers are what make the §8 retention metric real. A ladder of one-time depth
purchases leaves no recurring value and no reason for an app to come back.

---

## 4. Two funnels, one engine

Do not blend these. They are different people with different trigger moments.

**Developer funnel — primary, this is the wedge**

```
HN / GitHub / awesome-list  →  pip install  →  local scan  →  GitHub Action in CI
   →  wants history, deltas, a correct fix  →  paid cloud
```

Trigger: professional hygiene, or a scan that went red in CI. Sells on rigour and integration.

**Founder funnel — secondary, keep it cheap**

```
Reddit / SEO long-tail  →  free hosted URL scan  →  report  →  paid remediation + badge
```

Trigger: **a customer asked for a security review.** This is the highest-intent moment in the
entire market and it is a revenue problem, not a fear problem. Per brief §2, the Stanford finding
means fear-based pitches bounce — users believe AI code is *more* secure. Sell the unblocked deal.

We are not going to win the founder funnel head-on against 13 SEO-funded competitors. We serve it
because it converts at the questionnaire moment and costs little once the engine exists.

---

## 5. Channel priority

Ranked by expected return for a solo builder with no budget and limited evening hours.

| # | Channel | Effort | Payoff lands | Notes |
|---|---|---|---|---|
| 1 | **GitHub / OSS distribution** | Med | 2–8 weeks | README is the real landing page. Topics, awesome-lists, GitHub Action in Marketplace. |
| 2 | **The data study** (see `06`) | High | One shot, large | The single highest-leverage asset. HN front-page shaped. Reproducible *because* we're open source — no competitor can match that. |
| 3 | **Hacker News** | Low | Immediate, spiky | Show HN for the tool; the study as its own post. Two separate shots. |
| 4 | **Reddit** | Med, ongoing | 4–12 weeks | See §6 — your assumption about which subs needs correcting. |
| 5 | **SEO long-tail** | High | 3–9 months | Do *not* fight for head terms. See `06`. |
| 6 | **Discords** (Supabase, Lovable, Bolt) | Low | Ongoing | Best place for brief §11 validation conversations. Where the pain gets voiced first. |
| 7 | **Dev newsletters / awesome-lists** | Low | Weeks | Cheap backlinks and qualified traffic. |
| 8 | **Product Hunt** | Med | One shot, small | Low priority. Dev tools underperform there. Fire it once, late. |

---

## 6. On the micro-SaaS subreddits

You flagged these as the opportunity. They are worth using, but they are **secondary, not primary**,
and the reason is worth internalising:

r/SaaS, r/microsaas, r/indiehackers, r/SideProject are **founder-to-founder rooms**. They are
saturated with self-promotion, the readers are mostly other builders looking for ideas rather than
buyers, and "I built a thing" posts get sympathy upvotes that convert at roughly nothing. Posting
there feels like marketing and mostly is not.

Your actual users are in **build rooms**: r/Supabase, r/vibecoding, r/lovable, r/cursor, r/bolt,
r/replit, r/nocode, r/webdev, r/devops. People arrive there with the specific problem your tool
solves, already stated in their own words.

The micro-SaaS subs are still useful, for one specific message: **the security questionnaire
moment** — "a customer asked for a security review and I had nothing to send them." That is a
founder problem, not a developer problem, and those rooms are exactly where it gets discussed.
Different post, different sub, not the same content cross-posted.

Full sub-by-sub map, rules, and templates: `05-community-playbook.md`.

---

## 7. Twelve-week sequence

Assumes evenings/weekends and that M1–M4 land roughly on the brief's estimates.

**Weeks 1–2 — Foundations (no promotion yet)**
- Resolve the name (`01-naming.md`). Everything below bakes it in; renaming later breaks domains,
  badge URLs, package names, and backlinks.
- Rewrite the README as a conversion asset (`03-readme.md`).
- Publish `SECURITY.md`, `METHODOLOGY.md`, and an acceptable-use policy — see §9.
- Create the Reddit/HN/GitHub identity. Start reading the target subs daily. **Post nothing
  promotional.** Answer questions only.

**Weeks 3–4 — Credibility before traffic**
- Ship the GitHub Action.
- Run the calibration set (M4) and *record the numbers* — this is both product work and the
  study's dataset.
- 20 validation conversations (brief §11) via Discords and comment replies.

**Weeks 5–6 — First public shot**
- Show HN: the open-source scanner.
- Post to r/Supabase, r/webdev, r/devops with the CI angle.
- Submit to awesome-lists and dev newsletters.

**Weeks 7–9 — The study**
- Publish the aggregate scan study with methodology and false-positive rate (`06`).
- HN + r/netsec + r/programming. This is the reputation-defining asset; do not rush it.

**Weeks 10–12 — Monetise**
- Hosted product live, paid tier open.
- Comparison/alternative pages go up (`06`).
- Product Hunt.
- Begin the founder-funnel SEO long-tail.

---

## 8. Metrics

**Track:** CLI installs · GitHub Actions workflow installs · repeat scans per app (the retention
signal that separates us from the 13) · free→paid conversion at the questionnaire moment ·
**verified false-positive rate** (product *and* marketing metric) · qualified conversations from
brief §11.

**Ignore:** GitHub stars in isolation, Product Hunt rank, upvotes, impressions, total scans run.

**The one number that decides this business:** repeat scans per app after 30 days. If apps scan
once and never again, we have built a fourteenth one-shot scanner and the position has failed.

---

## 9. Guardrails — non-negotiable

Brief §4 governs the product. These are the marketing-specific extensions.

- **Never scan-then-cold-pitch.** Unsolicited "I found a vulnerability in your app, buy my
  product" reads as extortion regardless of intent, and creates a paper trail showing profit from
  unauthorised access. This ends careers. No exceptions, no DMs, no "just being helpful."
- **The study publishes aggregates only.** Tier A only on third-party apps. No app names, no
  URLs, no screenshots, no re-identifiable detail. Tier B results only from apps you built
  yourself.
- **Open source creates a new liability: other people's scanning.** Publishing a Tier B RLS
  prober means someone will point it at an app they don't own. Required before the repo goes
  public: an explicit consent flag for Tier B, prominent acceptable-use terms, conservative
  default rate limits, and no bulk/target-list input mode.
  Turn this into positioning — *the scanner that refuses to do the illegal thing.* Publish the
  ethics doc. None of the 13 have one.
- **No unverifiable authority claims.** A faceless brand cannot claim "built by a DevSecOps
  engineer" — unverifiable authority is worse than none. Demonstrate expertise through published
  methodology, correct answers in threads, and calibration data.
- **Re-verify every statistic before publishing.** Brief §2's figures (CVE-2025-48757, the
  Stanford 40%, the Lovable RLS percentages) are load-bearing for credibility. A security product
  citing a stale number does not recover.

---

## 10. Kill criteria (updated)

Brief §13 still applies. Add:

- The open-source scanner reaches negligible adoption after the study lands — the wedge failed,
  and without it we are a fourteenth entrant with a worse free tier.
- A well-funded competitor open-sources an equivalent scanner first. The window closes.
- Calibration (M4) cannot get the false-positive rate under control. This kills the *only*
  uncontested differentiator, not just a feature.
