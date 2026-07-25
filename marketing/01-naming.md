# Naming

## 1. Decision

**Resolved 2026-07-25.**

| | |
|---|---|
| Product | **Overshare** |
| Command / package | `overshare` |
| Primary domain | **oversharehq.com** |
| Tagline carries the category | "Find out what your app shows the public — on every deploy." |

```bash
pip install overshare
overshare https://myapp.com --fail-on high
```

**Still outstanding, and it is the real gate:** the trademark search. IP Australia and USPTO TESS,
classes 9 and 42. Check `Oversecured` hardest — an existing mobile app vulnerability scanner,
different word but same category and similar prefix. Nothing should be published until this clears.

---

## 2. Why the previous name was dropped

Not preference — a verified collision. The rejected name was **Leak**+**Scan** (written split here
so a find-replace can't rewrite this section again; see the warning at the end of this file).

**That domain on `.io` is a live product of exactly that name.** A data-breach search engine ("find
if your password has been compromised"), domain registered 2024-08-10, serving HTTP 200 behind
Cloudflare. Confirmed by fetching the page, not inferred. The `.com` has been registered since 2015.

Three consequences, any one of which is disqualifying:

1. **Trademark.** The test is likelihood of confusion, not string equality. An identically-named
   product in the same category, in the classes you'd file in, is the scenario that forces a
   rename after launch — exactly what §5 warns about.
2. **You would never rank for your own name.** Every search for it returns them, forever.
3. **Wrong register anyway.** Brief §2 concludes: sell the outcome, not the fear. "Leak" is the
   fear word, and it fights the trust-artifact positioning and the badge.

The pluralised `.com` and the `.com.au` were considered and rejected. Neither removes the collision —
pluralising an existing mark in the same class arguably worsens it, plural domains leak type-in
traffic to the singular, and `.com.au` requires an ABN while signalling "Australian small business"
for a product distributed globally via GitHub and PyPI.

---

## 3. Criteria used

- Short, typeable, unambiguous as a shell command
- **No same-category collision** — the test that killed the previous name, and the one that matters.
  Domain availability is secondary; every real English word has its `.com` taken by someone
- **No "vibe"** — saturated, and the term will date badly; this tool should outlive it
- **No "scan" suffix** — the market is already SupaScan, Scanbee, vibeappscanner, VibeCheck,
  CheckVibe, VibeShip, VibeEval, SecureVibing. Another `*scan` is camouflage, and roundup lists are
  how buyers meet this category
- Proof register, not fear register
- Doesn't over-narrow — brief §3 wants cross-platform, so nothing Supabase- or bundle-specific

---

## 4. Why Overshare

- **Describes the actual finding.** A missing CSP or a published source map isn't a *leak*, but it
  is oversharing. The word covers the whole severity range; "leak" only fits the catastrophic end.
- **Right register.** Wry rather than alarming, which matches the tone the README already sets
  ("a scanner that cries wolf gets ignored") and the brief's sell-the-outcome conclusion.
- **Ages independently** of the AI-codegen wave. Not `*scan`, not `vibe*`.
- **No collision.** No existing security or developer-tool product uses the name.
- **Memorable.** It raises a half-smile, which is why people retain it after one exposure.

**The known objection:** heard cold, it doesn't tell you it's a security scanner. That's true, and
it's normal — Snyk, Sentry, Docker, Terraform, Vercel, Semgrep and Trivy are all meaningless
without context. The name's job is to be memorable and ownable; the tagline explains. Nobody meets
this name in isolation — they meet it on a README or a landing page with the explanatory line
directly beneath.

The alternative was a descriptive name like `surfacecheck` (`.io` and PyPI free). Rejected because
descriptive marks are weak to trademark, compete against the generic phrase in search, and narrow
the product — `surfacecheck` and `bundlecheck` both box in a scanner that already does DNS, TLS,
headers and CT logs, with RLS next.

---

## 5. Availability

Checked 2026-07-25 via RDAP and the PyPI JSON API, both calibrated against known-good and
known-bad controls first. **RDAP "free" is a strong signal, not proof — confirm at the registrar
before paying.**

| Asset | Status |
|---|---|
| PyPI `overshare` | **free** — the one that matters most for `pip install` |
| npm `overshare` | free |
| `oversharehq.com` | **free — buy this** |
| `tryovershare.com`, `overshareapp.com` | free (alternates) |
| `overshare.io` / `.sh` / `.tools` / `.security` | free |
| `overshare.com` / `.dev` / `.app` | taken |
| GitHub org `overshare` | taken → use `oversharehq` |

**Do not buy** the registrar's upsell TLDs. `.tech` renews at ~$140/yr, `.world` ~$91, `.build`
~$71, against ~$15–20 for `.com`. The cheap first year is the hook. Also avoid hyphens
(`over-share.com`) — every spoken mention becomes "overshare, with a dash".

**On `.io`:** fine as a redirect, not as the primary. Its long-term future carries some uncertainty
as a ccTLD tied to the Chagos Islands sovereignty transfer. Low risk, but if it were ever retired
you want to lose a redirect, not your brand.

## 6. Remaining checklist

- [ ] **Trademark — IP Australia + USPTO TESS, classes 9 and 42.** The only check that can force a
      rename after launch
- [ ] Confirm `oversharehq.com` at a registrar and buy it
- [ ] Register PyPI `overshare` — free, and more painful to lose than a domain
- [ ] Register npm `overshare`
- [ ] Create GitHub org `oversharehq`
- [ ] Grab X and Reddit handles even if unused
- [ ] Check the word isn't awkward in another major language

## 7. Code rename — done 2026-07-25

The codebase now carries the new name throughout. Completed:

- Python package directory and every import, via `git mv` so history follows the rename
- `[project.scripts]`, project name and license in `pyproject.toml`
- `web/lib/brand.ts`, and the `OVERSHARE_*` environment variables across `Dockerfile`,
  `web/Dockerfile`, `docker-compose.yml` and `web/.env.example`
- `README.md`, `API_CONTRACT.md`, the build brief (now `overshare-build-brief.md`), and the
  scanner's outbound `User-Agent`, which pointed at the old domain

Two things this does **not** cover:

- The checkout directory is still named after the old product. Renaming it breaks running
  sessions, so it is left for whenever the repo is next cloned fresh.
- A stale `*.egg-info/` may linger from an earlier editable install. Harmless; cleared by a
  reinstall.

---

## 8. Warning: do not blindly find-replace this directory again

A global `s/oldname/overshare/g` across `marketing/` was run once and **corrupted this file**,
rewriting the section that explains why the old name was rejected into a claim that the *new* name
collides — the exact opposite of the truth. Sections 2, 3 and 7 above are now written without the
literal old string so the same script can't damage them twice.

If the rename gets re-run, check that §2 still describes the *rejected* name and not Overshare.
Historical references and code paths are the two things a blanket replace always breaks.
