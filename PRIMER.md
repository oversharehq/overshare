# Overshare, end to end

A primer. `OVERVIEW.md` is the reference you check while working; this is the
thing you read once, front to back, to hold the whole system in your head.

Written 2026-07-25. Where something is a plan rather than a fact, it says so.

---

## 1. The thesis, in one page

People are building and shipping real web applications using AI tools — Lovable,
Bolt, v0, Replit, Cursor. The applications work. The people shipping them often
cannot read what was generated well enough to know what it exposes.

The specific failure is narrow and repeatable. A generated app wires a database
client into the frontend. Sometimes it uses the key that is *meant* to be public,
and sometimes it uses the one that bypasses every access control you have. Both
keys look identical — same length, same shape, same position in the same
function call. One of them is a catastrophe and the other is correct, and nothing
in the build output tells you which you shipped.

Overshare looks at what an application hands to anyone who visits it, and tells
you what is in there.

The name is the argument. A published source map is not a *leak* — nobody broke
in. A missing Content-Security-Policy is not a *breach*. But your app is telling
strangers more than you meant it to. It is oversharing.

**The commercial bet is that finding problems is worthless and proving you fixed
them is valuable.** There are roughly a dozen competitors offering a free URL
scan. That layer is commoditised. What none of them do is live in your CI, run on
every deploy, and accumulate a record over time. That record — what regressed
between Tuesday and Thursday, and a badge you can show a customer who is asking
whether you are safe to buy from — is the part somebody pays for monthly.

---

## 2. Follow one scan all the way through

This is the fastest way to understand the system, because every component exists
to serve this path.

### Someone pastes `https://myapp.com` into the box

The browser posts it to the **frontend's own origin**, not to the scanner. The
Next.js app at `web/` receives it at `/api/v1/scans` and forwards it server-side
to the API over a private network.

That indirection is deliberate and it buys three things. The API never needs
CORS, because from its perspective every request is same-origin. The API needs no
public address at all, so there is no second door to rate-limit. And the backend
URL stays a *runtime* value, which means one built image can be promoted from
staging to production without rebuilding.

### The API decides whether to accept it

Before anything is queued, `POST /v1/scans` does three checks in order.

Is it a URL at all? A typo like `my app` is a `400` with a helpful message.

Is it *reachable and public*? This is the SSRF guard, and it is the most
security-sensitive code in the project. It resolves the hostname and rejects the
request if any resolved address is private, loopback, link-local or otherwise
not a public host. If it fails, you get a `422` — and deliberately **without
saying why**. The specific reason is a probe result about somebody else's
infrastructure, on an endpoint with no authentication. Telling a caller
"that resolved to 10.0.0.5" turns the scanner into a port scanner.

Have you had too many scans this hour? Rate limits are per client IP, which
only works because the frontend forwards the real address and the API is not
publicly reachable — otherwise anyone could set the header themselves.

If all three pass, a row goes in a table and you get a `202` with an id.

### Why it does not just scan there and then

A scan takes tens of seconds. It fetches a page, then several JavaScript
bundles, then probes a handful of paths, then does DNS and certificate
transparency lookups. Holding an HTTP request open that long is fragile — every
proxy between you and the user has an opinion about idle connections.

So the scan is a job. You get an id immediately and poll `GET /v1/scans/{id}`
until it reports `complete` or `failed`. The job table is a plain SQL table
rather than a queue service, on purpose: it moves to Postgres by changing a
connection string, and it does not tie the deployment to one cloud's messaging
product.

### The scan itself runs in a different process

A worker picks up the job. It marks the scan `running`, then hands the actual
work to a **separate operating-system process**.

That boundary matters. The scan downloads and parses JavaScript written by
someone you have never met, and makes HTTP requests to addresses that source
influenced. Running that inside the API process gave it the API's memory, its
file descriptors and its lifetime — one runaway allocation in a parser and the
whole service goes down, taking every other user's scan with it.

Now a bad scan kills one process. The parent notices, records the scan as
failed, and everything else keeps running. Only data crosses the boundary: the
child receives a URL and returns a dictionary. It has no database handle, so
even a fully compromised worker has nothing to write through.

Be clear about what this is and is not. It bounds the *damage*. It does not
restrict where the scan can *reach* — that is still the SSRF guard's job alone,
and there is no network-level egress control today.

### What the scan actually does

In order:

1. **Fetch the page.** If this fails, the scan is *failed*, not clean — an
   unreachable app must never produce a reassuring empty report.
2. **Check the response.** Security headers, CORS behaviour, TLS version and
   certificate, cookie flags.
3. **Find the JavaScript.** Parse the HTML for script tags, up to 25.
4. **Read each bundle**, looking for credentials. Also look in the HTML itself,
   because plenty of generated apps inline a config object right there.
5. **Follow source maps.** If a bundle publishes one, that is a finding on its
   own — it is your original source — and the map gets read for secrets too.
6. **Probe a few well-known paths**: `/.env`, `/.git/HEAD`, `/.git/config`,
   `/.aws/credentials`. Only paths, never parameters, and no brute-forcing.
7. **Fingerprint the stack.** Which backend, which builder, which framework.
8. **Look outward.** DNS, SPF/DKIM/DMARC, and certificate transparency logs for
   the staging subdomain you stood up once and forgot.

Then duplicate findings are collapsed and a score is computed.

### How a finding is decided — the important part

**Nothing is reported because it looks suspicious.** There is no entropy check,
no "this string looks random" heuristic.

The reason is concrete. Minified production JavaScript is *full* of high-entropy
strings that are not secrets: webpack chunk hashes, integrity digests, mangled
identifiers, inlined images. By the measure entropy actually takes, they are
indistinguishable from an API key.

So a finding needs one of two things. Either it matches a prefix the vendor
controls and issues for nothing else — `sk_live_`, `AKIA`, `ghp_` — or the thing
decodes and says what it is.

The Supabase case is the clearest. The safe key and the dangerous key are both
JWTs. Identical shape. So the scanner decodes the payload and reads the `role`
claim. `anon` is reported as *information*: it is public by design, and flagging
it as a leak is the single most common false positive in this category.
`service_role` is reported as *critical*, because the token itself says so.

The cost is accepted and it is real: **Overshare has false negatives.** A key in
a format nobody implemented is missed. That direction is chosen deliberately,
because the two errors are not symmetrical. A miss leaves you where you already
were. A false alarm sends you to rotate a production key at midnight for
nothing — and after that you stop believing the tool, including the time it is
right.

### Scoring

Each severity carries a penalty: critical 40, high 20, medium 8, low 3, info 0.
Score is 100 minus the total, floored at zero, then graded A to F.

One subtlety worth knowing: **a penalty applies once per check, not once per
occurrence.** The same leaked key found in three bundles is one key to rotate,
not three problems. Counting it three times would also mean an app that ships
one bundle scores better than an identical app whose build tool emits four —
which says something about their bundler, not their security.

### The report says what it did not check

Every report ends by naming its own blind spots: anything behind a login, key
formats it does not recognise, whether row-level security is actually enforced,
server-side flaws, anything assembled at runtime.

This is not modesty. Because detection is precision-first, the errors this tool
makes are *misses* — so a report that lists findings and stops invites exactly
the wrong conclusion from a clean result. The footer exists so that "no
findings" cannot be read as "you are secure."

---

## 3. Three front doors, one engine

The same scanner is reachable three ways, and they are not equally important.

**The CLI** — `pip install overshare && overshare https://myapp.com`. Talks to
the scanner directly, no API involved. Two dependencies, deliberately light.

**The GitHub Action** — the one the strategy is built on. It installs the
scanner, scans your deployed app, writes a SARIF file and uploads it to GitHub
code scanning, where findings appear in the Security tab with severity and
remediation, tracked as new, still open, or fixed across runs.

Two behaviours in it were chosen carefully. The report uploads *before* the job
is failed, because gating first would throw away the findings on precisely the
run that breaks your build. And a scan that could not run at all fails loudly
rather than reporting an empty, falsely clean result.

**The website** — the free URL scan. Genuinely useful, and strategically the
least important of the three, because a dozen competitors offer the same thing.

Why the Action matters most: nobody else is in CI. A one-shot web scan is a
single moment of attention. A CI check runs on every deploy forever, which is
both the only way the product stays in your life and the only way scan history
— the thing you would actually pay for — accumulates at all.

---

## 4. How the money is meant to work

Open the detection, charge for fixing and proving.

**Free, permanently:** the scanner, the CLI, the Action, all checks, all
findings, and generic remediation advice. Including the row-level-security check
when it exists. The free tier has to be at least as good as the incumbents' free
tier or there is no reason to arrive at all.

**~$19–29/month — "Prove it":** scan history and what changed between runs,
scheduled monitoring, alerts when something regresses, and a verifiable badge.
This is the entry rung because it is cheap to build — storage, a scheduler, a
public page — and because it sells at a specific moment: a customer sends you a
security questionnaire and you need an answer today.

**~$49–99/month — Remediation:** fixes written against your actual schema and
opened as a pull request. Prices higher because that is where the expensive part
lives and where the real defensibility is.

**$199–499 one-off — deep authenticated scan.** A one-off rather than a rung,
because you buy it when a specific deal demands it and then do not need it again
for months. It anchors against the €500–2,000 a manual technical due-diligence
review costs.

Three rules behind that shape, worth not relitigating:

- The row-level-security check stays free. It is the highest-value check in the
  product, and competitors already probe it in *their* free tiers. Paywalling it
  makes our free scan worse than theirs, which removes the reason to show up.
- Remediation is not the top of a depth ladder. It is the upsell from *any*
  finding, at the moment you see something red. Making someone upgrade twice —
  once to scan deeper, again to fix — adds friction exactly where intent peaks.
- The number to watch is **repeat scans per app after 30 days.** If apps scan
  once and never return, the strategy failed and this is a thirteenth one-shot
  scanner.

---

## 5. The five decisions that shape everything else

If you only remember five things about why the code looks like it does:

**Precision over recall.** No entropy heuristics, ever. One bad report destroys
trust permanently and you do not get it back. Every new pattern must add a
benign lookalike to the test bundle that asserts zero findings.

**Open core.** The detection engine is the free wedge; history, validated fixes
and the badge are the product. Open source is also what makes a faceless brand
credible in security — code replaces a founder's face.

**The API has no public address.** No CORS, no second door, no separate abuse
surface. Everything goes through the frontend.

**Scans expire after 30 days.** A stored scan is a vulnerability report about a
live application, frequently one the submitter does not own. Kept forever, the
database becomes a target list. Thirty days is also exactly where the paid tier
begins, which makes the privacy answer and the business model the same answer.

**Portability over platform features.** SQLite over a managed queue, Docker over
a provider runtime, a job table over a message bus. Nothing here is hard to move.

---

## 6. What is actually real today

Honest inventory, because a plan and a running system are easy to conflate.

**Real and verified.** The scanner: 27 checks, 17 secret patterns, 231 tests. The
API, the job store, the retention purge. The frontend and the proxy between them,
exercised end to end. Process-isolated workers, checked against a live API. SARIF
output, validated against the official schema. The GitHub Action, which runs
itself in CI on every push. Docker images for both services.

**Real but unproven.** The Fly deployment configuration exists and nothing has
ever been deployed with it. The Action's SARIF *upload* step has never executed,
because the repository is private and the upload API is unavailable there.

The rendered UI is no longer among these. On 2026-07-25 the frontend was restyled
as a technical document rather than a dashboard — paper, serif prose, mono data,
rules instead of cards — because the thing being sold is published calibration
and the page should look like something measured. Every surface was then checked
in a real browser at desktop and phone widths, and the report was checked under
print emulation, since that is the artifact a customer is handed. Chrome only;
Safari and Firefox are still unlooked at.

**Not built.** Row-level-security testing — every Supabase report currently says
so explicitly rather than implying a pass. Generated fixes: the `fix` field
exists in the API contract and is always `null`. Scan history, deltas, badges,
scheduling, accounts, billing — the entire paid product. Email capture for the
waitlist. Any network-level egress control.

**Not decided.** Nothing is deployed and no domain is bought. The trademark
search has not been run, which is why the repository is still private.

---

## 7. What could kill this

**A false positive on somebody's real app, early.** This is the one that ends
it, which is why the detection rule is absolute and why calibration is treated
as a milestone rather than a chore.

**Never running the calibration.** Publishing a measured false-positive rate is
the only claim no competitor is making. Until that number exists it is a design
property, not a differentiator — and the section reserved for it in
`METHODOLOGY.md` stays deliberately empty.

**Building the paid product before anyone repeats a scan.** The metric exists to
answer that question before the billing code does.

**The legal line.** Scanning something you do not own, at anything beyond the
passive tier, is a criminal offence in both relevant jurisdictions and good
intent is not a defence. The related trap is subtler: scan someone's app, find
something, then email them offering a fix. That is extortion-shaped regardless
of intent, and it creates a written record. `ACCEPTABLE_USE.md` is the boundary
and it is not decorative.

**A rename after launch.** Which is the entire reason the repository is private
tonight.

---

## 8. Where to look for what

| Question | File |
|---|---|
| How do I run it, what does it check | `README.md` |
| What's built, what's next, what breaks if I touch it | `OVERVIEW.md` |
| How is a finding proven, where is it blind | `METHODOLOGY.md` |
| What's the wire format between frontend and API | `API_CONTRACT.md` |
| How do I get it onto a server | `DEPLOY.md` |
| Where is the legal line | `ACCEPTABLE_USE.md` |
| How do I work on the UI without breaking the design | `web/README.md` |
| Who is this for, how is it sold | `marketing/00-strategy.md` |
| Why is it called this | `marketing/01-naming.md` |
| What was the original plan | `overshare-build-brief.md` |

And the shortest possible tour of the code: `overshare/scanner.py` is the whole
pipeline in one readable function. Start there.
