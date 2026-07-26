# Marketing

Written 2026-07-25, pre-launch. Read `00-strategy.md` first — everything else is downstream of it.

Since first writing, the scanner core, API, frontend, and the GitHub Action with its SARIF report
are all built, and the rename to Overshare is complete everywhere. Nothing is public yet: the
trademark search hasn't run, so the repo is private and nothing is deployed.

| File | What it's for | Who uses it |
|---|---|---|
| `00-strategy.md` | Market reality, position, open/closed boundary, channels, 12-week plan, guardrails | You |
| `01-naming.md` | Naming decision (**resolved**), evidence, and the availability checklist | You |
| `02-messaging.md` | ICP, positioning, value ladder, objection handling, voice | Source for all copy |
| `03-readme.md` | Public README draft — the highest-converting OSS asset | Replaces root `README.md` at launch |
| `04-landing-page.md` | Landing page copy — now the **spec of record** for the built page in `web/` | You + frontend |
| `05-community-playbook.md` | Reddit/HN/Discord map, templates, prohibitions | You, daily from week 1 |
| `06-content-and-seo.md` | The data study spec + keyword map + editorial calendar | You |
| `07-launch.md` | Pre-launch checklist, Show HN post, runbook | You, week 5+ |

## The three decisions these files rest on

1. **Position: open-core.** OSS scanner as the wedge, hosted cloud as the revenue. Chosen because
   the URL-scanner market now has ~13 entrants and free scanning, badges, and remediation guidance
   are all already commoditised. See `00-strategy.md` §1.
2. **Differentiator: calibration, not coverage.** Competitors advertise check counts; we publish a
   false-positive rate. Already enforced in code by
   `tests/test_secrets.py::test_benign_bundle_produces_no_findings`. The *number* still needs M4,
   which hasn't started — so the claim is currently a design property, not a measurement.
3. **Brand: faceless.** Open source is what replaces a founder's face — code is the credential.

## Naming

**Decided 2026-07-25: Overshare** · command `overshare` · site `oversharehq.com`.

It replaces **Leak**+**Scan** (written split, so a find-replace can't rewrite this line — see
below), which was dropped because a live product of that exact name in the same category already
owns the `.io`: a trademark collision and a permanent search problem. Full evidence and the rejected
candidates are in `01-naming.md`.

**The rename is complete in both `marketing/` and the code** — package, scripts, `OVERSHARE_*` env
vars, `web/lib/brand.ts`, the outbound `User-Agent`, and the checkout directory itself. See
`01-naming.md` §7.

⚠️ **Never run a blanket find-replace across this directory.** One was run during the rename and
corrupted `01-naming.md`, inverting the section explaining the *rejected* name into a claim that
Overshare itself collides. It damaged this file's naming section the same way. Historical references
are what a global replace always breaks.

## Do this first

Updated 2026-07-25. `OVERVIEW.md` §6–8 is the live status board for the whole project; this list is
just the marketing-blocking slice.

- [ ] **Trademark search — IP Australia and USPTO TESS, classes 9 and 42.** Check `Oversecured`
      hardest. The only check that can force a rename after launch, and nothing publishes until
      it clears
- [x] Create GitHub org `oversharehq` and push the code — done, but the repo is **private** until
      the trademark clears, so every "View on GitHub" CTA still 404s
- [ ] Flip the repo public and tag `v1` — `03-readme.md` and `04-landing-page.md` both ship a
      `uses: oversharehq/overshare@v1` snippet that cannot resolve until this happens
- [ ] Buy `oversharehq.com`; register PyPI + npm `overshare`; cut the PyPI release
- [x] Rename the package in code — done across the scanner, API, frontend and docs
- [ ] Create the Reddit/HN account and start participating (30-day age gates)
- [ ] Write `METHODOLOGY.md` — three other files link to it, and it needs M4 calibration data to be
      real
- [ ] Run competitors' free scans against your own test app and correct `00-strategy.md` §1
