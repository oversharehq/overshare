# Methodology

How Overshare decides something is worth reporting, what it deliberately will
not report, and where it is blind.

This document exists because a scanner's check count tells you nothing. Any
tool can claim 150 checks. The question that matters is how often it is wrong,
and in which direction.

---

## The one rule

**Every finding is structurally provable or anchored on a vendor-specific
prefix. Nothing is reported because it looks suspicious.**

There is no entropy scoring, no "high-randomness string" detection, no
machine-learning classifier. If a pattern cannot be made provable, it does not
ship.

### Why

The scanner reads minified production JavaScript. That code is *saturated* with
high-entropy strings that are not secrets: webpack chunk hashes, subresource
integrity digests, mangled identifiers, base64-encoded source maps, inlined
font and image data, cache-busting fingerprints, UUIDs.

An entropy threshold cannot separate those from a real credential, because on
the axis it measures they are identical. Every entropy-based scanner therefore
picks a point on a tradeoff: flag more real secrets and drown the user in
noise, or flag fewer and miss things. We reject the tradeoff by refusing to
guess.

The cost is real and we accept it: **Overshare has false negatives.** A
credential in a format we do not recognise will be missed. That is the
deliberate direction of the error, because the failure modes are not
symmetrical. A missed finding leaves you exactly where you already were. A
false finding sends you to rotate a production key at 11pm for no reason, and
after that you do not believe the tool again — including the time it is right.

Precision over recall. Stated up front, so you can decide whether that is the
trade you want.

---

## What "provable" means

Two things qualify.

**A vendor-specific prefix.** `sk_live_`, `AKIA`, `ghp_`, `github_pat_`,
`SG.`, `xoxb-`. These are namespaces the vendor controls and does not issue for
anything else. Matching one is not an inference about randomness; it is reading
a label the vendor wrote.

**Decodable structure.** Where a credential is a structured document, we parse
it and read the claim rather than guessing from the surrounding code.

The clearest case is Supabase. The anon key and the `service_role` key are both
JWTs. They are the same length, the same shape, and appear in the same
position in the same client call. Regex cannot tell them apart, and the
difference is the entire finding: the anon key is *designed* to ship to the
browser, while `service_role` bypasses Row Level Security completely.

So we decode the payload and read the `role` claim:

- `role: "anon"` → reported as **info**. This is normal and correct. Flagging
  it as a leak would be the single most common false positive in the category,
  and several tools do exactly that.
- `role: "service_role"` → reported as **critical**. Not a guess. The token
  says what it is.

The same principle covers database connection strings (parsed for an embedded
password rather than matched loosely) and private key blocks (matched on the
PEM armour, not on entropy).

---

## Severity, and what each level means

| Level | Meaning | Penalty |
|---|---|---|
| **Critical** | A credential or access path that is exploitable right now, by anyone, with no further work. A live `service_role` key. A readable `/.env`. | 40 |
| **High** | A serious weakness that needs a specific additional condition to be exploited, or exposes source and internals rather than access. Published source maps. A readable `/.git/config`. | 20 |
| **Medium** | A real weakness that raises the cost of other attacks or widens their impact. Missing CSP. CORS reflecting arbitrary origins. | 8 |
| **Low** | Hardening that is absent. Individually minor, and honestly labelled as such. Missing `nosniff`. Missing `Referrer-Policy`. | 3 |
| **Info** | Observed and reported, not a problem. Platform fingerprint. The Supabase anon key. DNS records. | 0 |

Severity is a property of the check, not of how alarming the string looks.

### Scoring

Score is `100 − total penalty`, floored at zero. Grades: **A** ≥ 90, **B** ≥ 75,
**C** ≥ 60, **D** ≥ 40, otherwise **F**.

**Penalties apply once per check, not once per occurrence.** One leaked Stripe
key found in three different bundles is one key to rotate, not three problems,
and scoring it three times would say something false about how much work you
have to do. It would also mean a site that ships the same bundle under four
filenames scores worse than an identical site that ships one — which is a fact
about their build tool, not their security.

---

## What it does not do

Overshare only looks at what your app already serves to anybody who visits it.

- **It does not log in.** No credentials, no authenticated crawling.
- **It does not write.** No POST, PUT, PATCH or DELETE to your app, ever.
- **It does not enumerate.** No directory brute-forcing, no parameter fuzzing,
  no user enumeration.
- **It does not exploit.** Where a weakness is detected, it is detected from a
  response, not by demonstrating impact.
- **It does not use the credentials it finds.** A discovered `service_role` key
  is reported and redacted; it is never used to connect to anything. Proving it
  works would be unauthorised access to your database.

Every secret is redacted before it reaches a report, a log, or the database:
enough characters to recognise which key it is, never enough to use it.

---

## Known blind spots

Stated because a scanner that only advertises what it catches is telling you
half of what you need.

- **Credentials in unrecognised formats.** Self-issued tokens, internal API
  keys, and any vendor whose prefix we have not implemented.
- **Anything behind a login.** The entire authenticated surface is invisible.
  Most real business logic lives there.
- **Runtime-only behaviour.** We fetch and parse without executing JavaScript,
  so a key assembled at runtime from fragments, or fetched from a config
  endpoint after load, is not seen.
- **Row Level Security enforcement.** We currently detect that a Supabase
  project is in use and report that RLS was *not tested*. Detecting a
  misconfigured policy requires actually querying the database, which is Tier B
  and needs your authorisation. Until then, an insecure RLS policy is a blind
  spot and the report says so rather than implying a clean bill.
- **Server-side vulnerabilities.** Injection, broken access control, insecure
  deserialisation. None of it is visible from outside.
- **Whether a finding matters to you.** We can prove a key is published. We
  cannot know it is a test key in a sandbox account.

A clean Overshare report means *the public surface we know how to check looks
right*. It does not mean the app is secure, and the report says that in those
words.

---

## Measured false-positive rate

> **Not yet measured.** This section is deliberately empty rather than filled
> with an estimate.
>
> The calibration run — every finding across 20–30 real applications verified
> by hand, and every false positive fixed or the pattern withdrawn — has not
> been done. When it has, the rate, the sample, the date and the method go
> here, along with the raw results.
>
> Publishing a number we have not measured would defeat the purpose of the
> document that publishes it.

What exists today is the design property, not the measurement: the test suite
includes a bundle of benign lookalikes — build hashes, SRI digests, example
keys from vendor documentation, anon JWTs — and
`tests/test_secrets.py::test_benign_bundle_produces_no_findings` asserts that it
produces **zero** findings. Every new pattern must add its own benign lookalike
to that bundle before it can ship.

That is a floor, not a false-positive rate. It proves the patterns do not fire
on the lookalikes we thought of.

---

## Reporting a false positive

A false positive is a bug of the highest severity in this project, and it is
treated as one.

Open an issue at
[github.com/oversharehq/overshare/issues](https://github.com/oversharehq/overshare/issues)
with the `false-positive` label. Include the `check_id`, and the surrounding
context if you can share it.

**Do not include the actual credential.** The redacted evidence string from the
report is what we need, and if it turns out we need more we will ask.

If a finding on a large real production site cannot be reproduced as a genuine
issue, the working assumption is that the pattern is wrong — not that the site
is unusual.

---

## Reproducing any of this

Detection lives in `overshare/checks/`. There is no hosted component involved in
deciding what is a finding; the CLI and the hosted scan run the same code, so
anything here can be verified against the source.

```bash
pip install overshare
overshare https://yourapp.com --json
```

Check identifiers are stable and are never renamed once shipped, because
scan-to-scan comparison keys off them.
