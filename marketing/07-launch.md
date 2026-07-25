# Launch

**Two launches, not one.** The tool (week 5–6) and the study (week 7–9). Separating them gives you
two shots at the same audiences with genuinely different content, and the study lands far harder
once people already have the tool installed.

Do not fire either until §1 is fully done. A launch you only get once, spent on a repo with a
broken link, is the most expensive mistake available here.

---

## 1. Pre-launch checklist

**Blocking — no launch without every one of these:**

- [ ] Name resolved and verified (`01-naming.md` §4 — including trademark)
- [ ] `pip install leakscan` works from a clean machine. Test on a machine that isn't yours
- [ ] README rewritten (`03-readme.md`)
- [ ] **`METHODOLOGY.md` exists and is real.** README and landing page both link to it. It is the
      single link a skeptical reader clicks. It cannot 404
- [ ] `LICENSE` (Apache-2.0), `SECURITY.md`, `ACCEPTABLE_USE.md`, `CONTRIBUTING.md`
- [ ] Tier B consent gate + conservative default rate limits + no bulk/target-list input
      (`00-strategy.md` §9 — this is what stops your tool becoming someone else's mass scanner)
- [ ] GitHub Action published and tested in a real repo
- [ ] Landing page live, scan box working, no placeholder text, no fake statistics
- [ ] Scan endpoint survives an HN front-page spike — rate limits, queue depth, a graceful
      "we're swamped, here's the CLI" fallback
- [ ] Every brief §2 statistic re-verified or removed
- [ ] Reddit/HN/GitHub account has ≥30 days age and genuine comment history (`05` §1)

**Strongly recommended:**

- [ ] Ran competitors' free scans against your own test app (brief §11) — you *will* be asked how
      you compare, and "I haven't tried them" is a bad answer
- [ ] 20 validation conversations done
- [ ] Someone else has run the tool and read the README cold
- [ ] Privacy policy + scan-retention answer decided (brief §12)

---

## 2. Launch one — the tool

### Show HN

Post Tue–Thu, roughly 8–10am US Eastern. Title format is strict:

> **Show HN: LeakScan – Open-source scanner for what your web app leaks publicly**

No superlatives, no "revolutionary," no emoji. HN titles that sell get flagged.

**First comment, posted by you immediately after submitting:**

> Author here. I built this after looking at how much AI-generated code ends up shipping secrets
> in the client bundle.
>
> The design decision I'd most like criticism on: it deliberately flags less than other scanners
> in this space. Nothing is detected on entropy, because minified bundles are full of build
> hashes, SRI digests and UUIDs that look exactly like leaked keys. Every pattern is anchored on a
> vendor prefix or an unambiguous structure, and there's a test that feeds in realistic lookalikes
> and asserts zero findings.
>
> The example I think is worth the most: a Supabase anon key and a `service_role` key are both
> JWTs with the same shape. The anon key is public by design and flagging it is just wrong. So it
> decodes the `role` claim instead of pattern-matching. `service_role` in a browser bundle bypasses
> RLS entirely and is the actual emergency.
>
> It also won't claim your app is clean when it can't know — passive scanning can't verify RLS is
> enforced, so the report says so rather than showing a green check.
>
> On legality, since it'll come up: passive checks fetch only what the server already sends every
> visitor. No writes, no logins, no enumeration, no credential that wasn't already public. The
> fetcher resolves the host, rejects any non-public address, and connects to the pinned IP to close
> DNS rebinding. There's an acceptable-use policy in the repo, and the one thing I ask is that
> nobody scans apps they don't own and then cold-pitches the owner.
>
> There's a deliberately vulnerable app in `testdata/` so you can see what it catches and what it
> misses before trusting it. Measured false-positive rate is in METHODOLOGY.md.
>
> Happy to take apart any detection pattern you think is wrong.

**Why this comment works:** leads with a tradeoff rather than features, pre-answers the legality
question that would otherwise dominate the thread, demonstrates real expertise through the
anon-vs-service_role distinction, and explicitly invites attack. HN rewards all four.

**Rules:** never ask anyone to upvote. Reply to every comment, especially hostile ones. If someone
finds a false positive, thank them, fix it, and link the commit in-thread — that exchange is worth
more than the post.

### Reddit

Templates in `05-community-playbook.md` §4. Stagger across several days, tailored per sub, never
the same text twice. r/Supabase first — it's the best fit and the friendliest technical audience.

### Everything else, launch week

- Submit to awesome-security / awesome-selfhosted / relevant awesome-lists (PRs)
- GitHub topics set
- Post in Supabase and Lovable Discords **only where a #showcase or #tools channel exists** —
  never in #help
- Dev newsletters that accept submissions

---

## 3. Launch two — the study

Same channels, higher-value content, plus the doors that were closed to a product post: **r/netsec
and r/programming**.

> **Show HN: We scanned N public AI-built apps – findings, and our false-positive rate**

Frame as research. The product is a footnote at the bottom, not the lede. Full spec in
`06-content-and-seo.md` Part 1.

This is the post that defines your reputation in this space. If the tool launch underperforms,
this one still works. If you have to choose one to get right, choose this.

---

## 4. Product Hunt

Low priority — dev tools underperform there and it's a single non-repeatable shot. Fire it in week
12, after the study, when you have real numbers and testimonials. Not before.

---

## 5. Launch day runbook

**Morning:** submit, post your first comment immediately, then leave it alone. No refreshing.

**All day:** reply to every comment within ~30 minutes. Watch error rates and queue depth on the
scan endpoint. Keep a running list of every false positive reported.

**Do not:** argue with anyone, ask for upvotes, cross-post the same text everywhere, or ship code
changes mid-thread beyond genuine hotfixes.

**Evening:** post a short "here's what got fixed today from your feedback" comment. It converts
critics and it's the clearest possible demonstration that false positives are treated as bugs.

**Next day:** open a GitHub issue for every reported FP. Reply to each reporter when it's fixed.

---

## 6. Failure modes

| Risk | Mitigation |
|---|---|
| **A false positive found publicly on launch day** | Near-certain, and survivable. Fix fast, in public, and thank them. The recovery is better marketing than a clean launch |
| **"This is just X but open source"** | True and fine. That *is* the position. "Yes — and you can read the code and run it in CI" |
| **"Isn't this illegal?"** | Pre-answered in the first comment. Have the acceptable-use policy live |
| **Someone mass-scans with your tool** | The reason the consent gate and rate limits are blocking items. Have a public response ready |
| **Scan endpoint melts** | Rate limit, queue, and a graceful fallback pointing at the CLI |
| **Nobody cares** | The likeliest outcome of any single launch. That's why there are two, plus the SEO long tail. Do not read one quiet launch as a kill signal — `00-strategy.md` §10 defines the real ones |
