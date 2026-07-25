# Naming

**Decision needed before:** anything is published. Domains, package names, GitHub org, badge URLs,
and backlinks all break on a rename. Right now the cost of changing is one find-replace. After the
study lands it is weeks of work and lost SEO.

**Nothing below has been verified for availability.** Run §4 before committing.

---

## 1. The case against "LeakScan"

Not a bad name. Three specific problems, in order of severity:

1. **It is camouflage in this market.** The space is already SupaScan, Scanbee, vibeappscanner,
   VibeCheck, CheckVibe, VibeShip, VibeEval, SecureVibing, checkmyvibeapp. Another `*scan` name is
   indistinguishable in a list — and lists are literally how buyers encounter this category now
   ("best vibe coding security scanners 2026" roundups).
2. **Fear register, which your own brief flags as wrong.** Brief §2 concludes: sell the outcome,
   not the fear, because users don't believe they're vulnerable. "Leak" is the fear word. It
   fights the trust-artifact positioning and the badge.
3. **It describes a one-shot event.** Our entire differentiation is that this runs continuously in
   CI. "Scan" is a noun-moment; the position is a habit.

Also unverified for .com/.dev, PyPI, npm, and trademark (brief §12 open question, still open).

## 2. Criteria

- Short, typeable, unambiguous as a shell command
- **No "vibe"** — saturated, and "vibe coding" will date badly; this tool should outlive the term
- **No "scan" suffix** — see above
- Available as GitHub org + PyPI + npm + domain
- Trust/proof register, not fear register
- Doesn't over-narrow (not Supabase-only, not Lovable-only — brief §3 wants cross-platform)

## 3. Shortlist

### Recommended: **plainsight**

```bash
plainsight https://myapp.com
plainsight --fail-on high        # in CI
```

- **Describes the product precisely.** Tier A fetches only what the app already serves to any
  visitor. The exposure was always in plain sight; we just look. That is the whole product.
- **Carries the legal posture for free.** "We only look at what's in plain sight" is the
  one-sentence version of brief §4's authorisation model. Useful for the ethics doc, and it
  preempts "is this legal?" — which will be the top comment on every HN and Reddit post.
- Not fear-framed, not vibe-framed, no scan suffix, ages independently of the AI-codegen wave.
- One word, reads as a real product, works as a GitHub org.

Risk: two syllables of abstraction — doesn't say "security" on its own. Acceptable for a dev tool
where the tagline does that work; would be weaker for a pure consumer SaaS.

### Alternates

| Name | Angle | Watch out for |
|---|---|---|
| **frontage** | What's visible from the street. Same logic, more architectural. | Real-estate connotation. |
| **bystander** | What any passer-by could see — the exact legal standard for Tier A. | Slightly passive/negative ("bystander effect"). |
| **glasshouse** | "Your app is a glass house." Vivid, memorable. | Faintly accusatory; longer. |
| **curbside** | Curb appeal — what anyone sees without entering. | Reads retail/food-pickup. |

### Rejected

`shipcheck`, `shipsafe`, `safeship` — **SafeToShip and ShipSecure both already exist** in this
exact market. Direct collision.
`greenlight` — multiple existing security/compliance companies (Lightship's Greenlight, Greenlight
Guru). Contested.
`attest` — generic, crowded in compliance tooling, weak as a command.

## 4. Availability checklist

Run all of these before committing. Fifteen minutes.

- [ ] Domain: `.com` and `.dev` — check on a registrar directly, not a suggestion tool
- [ ] GitHub organisation name free
- [ ] PyPI project name free (`pip index versions <name>` / pypi.org/project/<name>)
- [ ] npm package name free — needed if a Node wrapper or Action ever ships
- [ ] Trademark: search your own jurisdiction (IP Australia) **and** USPTO TESS, class 9 and 42
- [ ] Existing product collision: plain web search + a search restricted to GitHub
- [ ] Social handles: X, Reddit — grab even if unused
- [ ] Not an offensive/awkward word in another major language

**Trademark is the one that can force a rename after launch.** Do not skip it. A security brand
that has to rebrand mid-flight loses the trust it spent months accumulating.

## 5. If you keep LeakScan anyway

Defensible if you'd rather not spend the cycles. In that case:

- Lean the *tagline* hard toward proof, to offset the fear register: e.g. "Know what your app
  shows the public — on every deploy," not "Find your leaks."
- Still verify §4 before publishing. The name being unverified is a live risk today.
- Expect to spend more copy explaining continuous/CI, since the name works against it.

## 6. Decision

**Resolved 2026-07-25: the name stays `LeakScan`, command `leakscan`.** The case in §1 was heard
and overruled. All `{{NAME}}`/`{{CMD}}` placeholders across `marketing/` have been replaced.

§5 is therefore live, not hypothetical — the copy now has to do the work the name does not:

- The landing H1 is "Know what your app shows the public," not a leak-framed line, to keep the
  page in the proof register.
- Continuous/CI gets its own section rather than being implied, because "scan" reads one-shot.

In the codebase the name is centralised so a reversal stays cheap: `web/lib/brand.ts` on the
frontend, `[project.scripts]` in `pyproject.toml` for the command.

**Still outstanding — §4 was not run.** Domain, PyPI, npm, GitHub org and trademark are all
unverified. Trademark is the one that can force a rename after launch; it needs a search of
IP Australia and USPTO TESS, classes 9 and 42, before anything is published.
