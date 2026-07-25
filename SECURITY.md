# Security policy

Overshare is a security tool, which makes a vulnerability in it worse than
average: it runs against targets people care about, and the hosted service
accepts a URL from anyone on the internet and fetches it.

Reports are genuinely welcome and will not be met with lawyers.

## Reporting

Use **GitHub private vulnerability reporting** — the *Report a vulnerability*
button under the Security tab of
[oversharehq/overshare](https://github.com/oversharehq/overshare/security).
It is private between you and the maintainers, and it does not require finding
an email address or trusting one.

Once `oversharehq.com` is live, `security@oversharehq.com` will work as an
alternative. Until then, the GitHub route is the only channel — please do not
open a public issue for a vulnerability.

**Please do not** open a public issue, post it publicly, or demonstrate it
against the hosted service beyond what is needed to confirm it exists.

Useful in a report: what you did, what happened, what you expected, and why it
matters. A proof of concept helps. A full exploit chain is not required.

## What to expect

This is maintained by one person, in evenings and weekends. Honest timelines
rather than flattering ones:

- **Acknowledgement:** within 5 days.
- **Assessment and a plan:** within 14 days.
- **Fix:** as fast as severity warrants. A critical issue in the SSRF guard or
  in secret redaction gets same-week treatment.

You will be credited in the advisory and the release notes unless you would
rather not be. There is no bug bounty — no budget for one, and saying so is
better than an unfunded promise.

## Scope

**In scope**

- The scanner core, the CLI, and the GitHub Action (`overshare/`, `action.yml`).
- The HTTP API (`overshare/api/`).
- The web frontend and its proxy (`web/`).
- The hosted service at `oversharehq.com`, once it exists.

**Especially interesting**, because these are where a bug is worst:

- **SSRF bypass.** `fetch/ssrf.py` validates and pins a URL to a resolved
  public IP, and `fetch/client.py` re-applies that policy on every redirect
  hop. Anything that reaches a private address, or that changes the target
  between validation and connection, is a serious finding.
- **Secret leakage.** A credential reaching a report, a log, or the database
  unredacted. See `findings/model.py::redact`.
- **A false negative that is systematic** — a class of secret the scanner
  should catch and provably does not.
- **Result poisoning.** Anything that makes a scan report a clean result for an
  application that is not clean. A scanner that lies is worse than no scanner.

**Out of scope**

- Findings in applications *scanned by* Overshare. Those belong to the owner of
  that application, not here.
- Missing hardening headers on the marketing site, absent a demonstrated
  impact.
- Rate limits being reachable. They are deliberately low; tell us if they can
  be *bypassed*.
- Automated scanner output with no analysis.
- Denial of service through raw volume.

## Safe harbour

If you make a good-faith effort to follow this policy, we will not pursue or
support legal action against you for your research, and we will treat it as
authorised.

Good faith means: only test against your own installation or the hosted service,
stop as soon as you have confirmed a problem, do not access or modify data that
is not yours, do not degrade the service for others, and give us a chance to fix
it before going public.

That protection is ours to give and does not bind third parties — including the
owners of applications you might scan. See [ACCEPTABLE_USE.md](ACCEPTABLE_USE.md).

## Supported versions

Pre-1.0. Only the latest release is supported; fixes land on `main` and in the
next release rather than being backported.
