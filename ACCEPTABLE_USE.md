# Acceptable use

Overshare points a scanner at a web application. That is a capability that is
legitimate when you own the target and a criminal offence when you do not, so
the boundary matters more than it does for most developer tools.

Under Australia's **Criminal Code Act** and the US **Computer Fraud and Abuse
Act**, unauthorised access to a computer system is the offence. Good intent is
not a defence. This applies to you when you run the CLI, and to us when we run
a scan you submitted.

> **Also published at `/acceptable-use`.** The website cannot read this file at
> build time, so the page restates it. Headings, the scan tiers and the
> retention window live once in `web/lib/docs.ts`, and
> `tests/test_docs_sync.py` fails CI if this file, that file and the API's
> `OVERSHARE_RETENTION_DAYS` default stop agreeing. Change the retention
> promise here and the Python suite goes red until the code matches.

---

## The short version

**Scan applications you own, or that you have written permission to test.
Nothing else.**

---

## What the scanner does by default

The default scan — the CLI, the GitHub Action, and the scan box on the website
— is **passive**. It requests only what the application already serves to any
member of the public: the page, its JavaScript bundles, its response headers,
its TLS configuration, public DNS records, and certificate transparency logs.

It does not log in, does not send POST/PUT/PATCH/DELETE, does not
brute-force paths or parameters, and does not use any credential it discovers.

A passive scan of a public URL is, in itself, ordinary web traffic. That is why
the default carries no authorisation requirement. It is not a licence to point
it at anything you like for any purpose — see prohibited uses below.

## Scan tiers and what each requires

| Tier | What it does | Authorisation |
|---|---|---|
| **A — Passive** | Fetches what the app serves to any visitor. | None. |
| **B — Anon-key read** | Uses the client-side key the app already ships to every browser, to make the same read any visitor's browser could. This is the Row Level Security check. | The owner must have submitted the app themselves, or given permission. |
| **C — Authenticated** | Owner-supplied credentials, deeper probing. | **Written owner authorisation. Always. No exceptions.** |

Tier B is not implemented yet. When it is, the discipline will be structural
rather than conventional: single-row reads, rate limited, no writes, no
enumeration. Prove the door is unlocked; do not walk through it.

---

## Prohibited

- **Scanning an application you neither own nor have permission to test**,
  beyond a passive scan, at any tier.
- **Using Overshare as reconnaissance for an attack.** Establishing what an
  application exposes in order to exploit it is unauthorised access, and the
  scan is evidence of intent.
- **Scan-then-pitch.** Running a scan against someone else's application and
  contacting them to sell a fix reads as extortion regardless of how it was
  meant, and creates a written record of profiting from an unsolicited scan.
  We will not do this, and you may not do it with output from this tool.
- **Publishing findings about a third party's application** without giving them
  private notice and reasonable time to fix it.
- **Using a discovered credential.** A key found in a bundle is reported and
  redacted. Connecting to anything with it is unauthorised access to a system,
  and the fact that the key was carelessly published is not a defence.
- **Volumetric use.** Automating Overshare to sweep large numbers of
  third-party applications. The rate limits are not the policy; this is.
- **Circumventing the SSRF protections** to reach internal or private-network
  addresses. The `--unsafe-allow-private-ips` flag exists for scanning your own
  local test app and logs a warning saying so. Using it against infrastructure
  that is not yours is exactly the conduct the guard is there to prevent.

---

## If you find something in someone else's application

It happens — you scan your own app and a shared dependency, a subdomain, or a
misconfigured third-party service surfaces.

Disclose it privately to the owner, give them time to fix it, and publish
nothing in the meantime. Do not offer them a paid fix in the same message.

---

## What we do with scans submitted to the hosted service

- Scan results are **kept for 30 days and then deleted automatically.**
- Secrets are redacted before a result reaches a report, a log, or the
  database. Enough characters survive to identify which key it is, never enough
  to use it.
- We do not contact the owners of scanned applications.
- We do not sell scan data, and we do not use it to approach anyone
  commercially.

The privacy consequence worth stating plainly: anyone can submit any URL to the
public scan box, so a scan of your application may exist because someone else
submitted it. That result is a report on your public surface, it expires in 30
days, and if you want it gone sooner, ask.

---

## Enforcement

We can decline or block scans, and we can rate-limit or ban clients. We would
rather explain a boundary than enforce one, so if your use case sits near a
line here, ask first.

## Questions

Open an issue at
[github.com/oversharehq/overshare/issues](https://github.com/oversharehq/overshare/issues)
for anything that is not itself sensitive. For a suspected vulnerability in
Overshare, see [SECURITY.md](SECURITY.md).

---

*This document describes how the project expects its tool to be used. It is not
legal advice, and it does not override the law in your jurisdiction, which may
be stricter.*
