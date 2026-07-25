# Marketing

Written 2026-07-25, pre-launch. Read `00-strategy.md` first — everything else is downstream of it.

| File | What it's for | Who uses it |
|---|---|---|
| `00-strategy.md` | Market reality, position, open/closed boundary, channels, 12-week plan, guardrails | You |
| `01-naming.md` | **Blocking decision.** Shortlist + availability checklist | You, this week |
| `02-messaging.md` | ICP, positioning, value ladder, objection handling, voice | Source for all copy |
| `03-readme.md` | Public README draft — the highest-converting OSS asset | Replaces root `README.md` at launch |
| `04-landing-page.md` | Full landing page copy | Frontend agent |
| `05-community-playbook.md` | Reddit/HN/Discord map, templates, prohibitions | You, daily from week 1 |
| `06-content-and-seo.md` | The data study spec + keyword map + editorial calendar | You |
| `07-launch.md` | Pre-launch checklist, Show HN post, runbook | You, week 5+ |

## The three decisions these files rest on

1. **Position: open-core.** OSS scanner as the wedge, hosted cloud as the revenue. Chosen because
   the URL-scanner market now has ~13 entrants and free scanning, badges, and remediation guidance
   are all already commoditised. See `00-strategy.md` §1.
2. **Differentiator: calibration, not coverage.** Competitors advertise check counts; we publish a
   false-positive rate. This is already enforced in code by `test_secrets.py`.
3. **Brand: faceless.** Open source is what replaces a founder's face — code is the credential.

## Naming

**Decided 2026-07-25: `LeakScan` / `leakscan`.** Placeholders are gone from every file here.
See `01-naming.md` §6 for what that commits the copy to, and §4 for the availability checks
that have *not* been run.

## Do this first

- [ ] Trademark search — IP Australia and USPTO TESS, classes 9 and 42. The only check that can
      force a rename after launch
- [ ] Domain, PyPI, npm and GitHub org availability for `leakscan`
- [ ] Create the Reddit/HN account and start participating (30-day age gates)
- [ ] Write `METHODOLOGY.md` — three other files link to it
- [ ] Run competitors' free scans against your own test app and correct `00-strategy.md` §1
