# Community playbook — Reddit, HN, Discord

The tactical file. `00-strategy.md` §5–6 has the reasoning; this is what to actually do.

**Verify before relying on this:** subreddit names, rules, and moderation change constantly. Read
each sub's sidebar and rules page yourself before your first post. Several subs below may have
been renamed or merged.

---

## 1. The faceless-brand problem, solved

You chose a faceless product brand. Reddit is the hardest channel for that, because Reddit
detects and punishes brand accounts hard. Posting as `OvershareOfficial` gets you downvoted,
reported, and shadowbanned.

**The resolution: be a person, not a persona, and let the project be a project.**

On Reddit and HN you are a human who maintains an open-source tool. That's the most normal
identity on the internet and it requires no real name, no face, no LinkedIn, no credentials.

- **Do:** one consistent personal handle. Real comment history across your genuine interests.
  "I maintain an open-source scanner that does this" when relevant.
- **Don't:** a brand account. Multiple accounts. Any claim like "as a DevSecOps engineer…" —
  unverifiable authority from an anonymous account reads as a lie and is worse than saying nothing.
- **Instead of claiming expertise, demonstrate it.** Answer an RLS question correctly and in
  detail, with no link. That does more than any credential claim, and it's the one thing the 13
  competitors' marketing teams can't fake.

**Start the account in week 1, not week 5.** Many target subs gate on account age (often 30+ days)
and karma. An account created the day you launch cannot post in the subs that matter.

---

## 2. Subreddit map

Priority: **P1** = where your users are · **P2** = worth a tailored post · **P3** = one shot, high risk.

### P1 — build rooms (people with the problem, right now)

| Sub | Why | Angle | Promo tolerance |
|---|---|---|---|
| **r/Supabase** | The single best sub for this product. RLS is a constant topic. | Answer RLS questions properly. The `service_role` vs anon-key distinction is your calling card. | Low for promo, high for genuinely useful tools |
| **r/webdev** | Large, developer-heavy | CI integration, "what your bundle leaks" | Strict. Read rules twice |
| **r/devops** | CI/CD native audience | The GitHub Action, `--fail-on` in pipelines | Moderate, hates fluff |
| **r/vibecoding** | Exactly the target market | Practical "before you ship" checklist | Higher tolerance, lower technical depth |
| **r/nextjs**, **r/reactjs** | Where the bundles come from | Source maps, env vars leaking into client bundles | Strict |
| **r/Firebase** | Firebase rules equivalent | Secondary until Firebase checks are strong | Moderate |
| **r/cursor**, **r/replit**, **r/ClaudeAI**, **r/ChatGPTCoding** | AI-assisted devs who *do* install CLIs | "Add this to your pipeline" | Varies widely |

Also check for a Lovable and a Bolt sub — names shift; find the active ones.

### P2 — founder rooms (the questionnaire moment)

| Sub | Angle |
|---|---|
| **r/SaaS**, **r/microsaas** | "A customer asked for a security review and I had nothing to send." Not the CLI post. |
| **r/IndieHackers**, **r/SideProject**, **r/EntrepreneurRideAlong** | Same. Feedback-request framing works better than announcement framing. |

These are the subs you flagged. Use them — but for the founder message only, and expect lower
conversion than the P1 build rooms. They're full of builders, not buyers.

### P3 — credibility rooms (the study only, one shot each)

| Sub | Requirement |
|---|---|
| **r/netsec** | Very high bar. Only the data study with full methodology. A product post gets removed instantly. |
| **r/programming** | The study, framed as research, never as a product |
| **r/opensource**, **r/coolgithubprojects** | The repo. Low risk, low reward |
| **r/cybersecurity**, **r/AskNetsec** | Participate; almost never post |

**Do not post the same content to multiple subs.** Cross-posting identical text is the fastest way
to get flagged as spam across all of them.

---

## 3. Rules of engagement

1. **Read the rules of every sub before posting.** Many ban self-promo outright; some have a
   dedicated promo thread; some require flair.
2. **90/10.** Nine genuinely useful contributions for every one that mentions your project. This
   is not a guideline, it is how you avoid a ban.
3. **Message the mods first** in strict subs. "I maintain an open-source tool relevant to this sub
   — is a post about it acceptable, and in what form?" This is underused and works remarkably
   often. A mod-sanctioned post can't be removed for self-promo.
4. **Never DM anyone about the product.** Ever. See §6.
5. **Disclose affiliation every single time.** "Disclosure: I maintain this." Non-negotiable —
   getting caught not disclosing ends the account and the brand.
6. **Answer the question first, mention the tool second, or not at all.** If your comment is only
   useful as a vehicle for the link, don't post it.
7. **Take the criticism.** Security audiences are hostile to new tools by default and they're
   right to be. Someone finding a false positive publicly is a gift — fix it, reply with the
   commit. That exchange converts better than any post.

---

## 4. What to post

### The comment (your main activity — do this daily, from week 1)

Search the P1 subs for `RLS`, `service_role`, `anon key`, `exposed API key`, `is my app secure`,
`source map`. Answer properly. No link.

> Worth separating two things that often get conflated: the anon key is *supposed* to be in your
> client bundle — it's public by design and it's not a leak. What actually matters is whether RLS
> is enforced behind it, because the anon key with RLS off means anyone can read your tables
> directly.
>
> The one that's a genuine emergency is `service_role`. It bypasses RLS entirely, so if it ever
> reaches the browser, nothing else you've configured matters. Both are JWTs and they look
> identical at a glance — decode it and check the `role` claim.
>
> Quickest check: open your deployed bundle, search for `eyJ`, decode what you find.

That comment sells nothing and is the most valuable marketing you can do. It establishes the exact
expertise that separates you from the 13, and people remember who gave them a straight answer.

### The launch post (r/Supabase, r/webdev, r/devops — week 5–6)

Tailor per sub; never paste the same text twice.

> **Open-source scanner that checks what your deployed app leaks in its JS bundle**
>
> I've been building a passive security scanner for AI-generated web apps. It fetches only what
> your app already serves to any visitor — the bundle, headers, TLS, DNS — and reports exposed
> secrets and misconfiguration. Apache-2.0, runs locally or in CI.
>
> The design decision I'd most like feedback on: it flags *less* than other scanners in this
> space. Nothing is detected on entropy, because minified bundles are full of build hashes that
> look exactly like secrets. Every pattern is anchored on a vendor prefix or structure, and there's
> a test that feeds in realistic lookalikes and asserts zero findings.
>
> It also refuses to imply your app is clean when it can't know — passive scanning can't prove RLS
> is enforced, so the report says that explicitly rather than showing a green check.
>
> There's a deliberately vulnerable app in the repo to see what it catches and what it misses.
>
> Disclosure: I maintain it. Free and open source, no account. Genuinely after feedback on the
> detection patterns — false positives are the failure mode I care most about.
>
> [link]

Why this works: leads with a design tradeoff rather than a feature list, invites critique, and the
"flags less" angle is counter-positioning nobody can copy without rebuilding.

### The founder post (r/SaaS, r/microsaas — week 6+)

Completely different post.

> **Anyone else get blindsided by a customer asking for a security review?**
>
> Curious how others handled this. You ship something, get real users, and then a bigger customer
> asks what your security posture is — SOC 2, a pentest report, anything. And you have nothing to
> send, so the deal stalls.
>
> Have you hit this? What did you actually send them?
>
> (Disclosure so I'm not being sneaky: I'm building something in this space, which is why I'm
> asking. Not linking it — genuinely want to know how people handle it.)

Not linking is deliberate. This is a brief §11 validation conversation that also builds
credibility. The people who reply are your qualified pipeline, and you can follow up when you
launch — *because they engaged first*.

### The study post (week 7–9)

The highest-value post you will make. Spec is in `06-content-and-seo.md`.

---

## 5. Discord

Better than Reddit for brief §11 validation, worse for reach. Supabase, Lovable, Bolt, and Replit
all have active servers.

- Join in week 1. Read `#help` channels daily.
- Answer questions. Same rules — no links unless asked.
- **This is where you find your 20 validation conversations.** People post real problems with real
  context, and a DM asking "mind if I ask how you handled X?" is acceptable here *when they raised
  the topic first* — unlike Reddit, where you never DM.
- The brief §11 questions to work toward, without interrogating: has a customer ever asked you for
  a security review? did it delay a deal? what did you do about security before launching? would a
  report you could hand a customer be worth anything?

---

## 6. Hard prohibitions

These are legal and reputational, not stylistic. Violating any one of them can end the project and
your career (brief §4).

- **Never scan an app you don't own and then contact the owner.** Not on Reddit, not by DM, not
  "just being helpful." Unsolicited "I found a vulnerability in your app, here's my product" is
  extortion-shaped regardless of intent, and it creates a written record of profiting from
  unauthorised access.
- **Never post findings about an identifiable third-party app.** No names, no URLs, no
  screenshots, no "a popular app I scanned." Aggregate and anonymised only.
- **Never run Tier B against anything you don't own** to generate content.
- **Never use multiple accounts, vote manipulation, or fake questions you then answer.** It always
  surfaces, and for a security brand it's fatal.
- **Never DM about the product on Reddit.**
- If a real vulnerability in a third party surfaces incidentally: private responsible disclosure,
  time to fix, nothing public.

---

## 7. Weekly cadence

Sustainable on evenings/weekends. Consistency beats intensity — 20 minutes daily outperforms a
launch-week blitz.

| | |
|---|---|
| **Daily, 15–20 min** | Read P1 subs. Answer 1–2 questions properly. No links. |
| **Weekly** | One substantive contribution — a detailed answer, a small write-up. Check Discord `#help`. |
| **Monthly** | One real post. Alternate: P1 technical → P2 founder → P3 study/research. |
| **Always** | Reply to every comment on your own posts within a few hours. Especially the critical ones. |

**Before launch week, you should already have three months of ordinary comment history.** That
history is what makes the launch post land as a maintainer sharing work rather than a marketer
arriving.
