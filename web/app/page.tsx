import Link from "next/link";
import { CommandBlock } from "@/components/CommandBlock";
import { Code, Figure, Note, Prose, Section, Shell } from "@/components/Paper";
import { ScanForm } from "@/components/ScanForm";
import { Todo } from "@/components/Todo";
import { BRAND, GITHUB_URL } from "@/lib/brand";
import { PLATFORMS } from "@/lib/platforms";

// Verbatim from a real run against testdata/serve_vulnerable_app.py. The
// marketing spec forbids stock illustrations here, and it doubles as the
// invitation in the open-source section to reproduce it.
const TERMINAL_OUTPUT = `${BRAND.name} report: http://localhost:8000/
 Score: 0/100   Grade: F   Scanned 5 asset(s) in 0.5s
 Findings: 11 critical  2 high  5 medium  2 low  6 info
 Platform: backend=supabase, builder=lovable

 CRITICAL  Supabase service_role key in client bundle
   where: /assets/index-a3f2b891.js
   evidence: eyJhbGciOi**********c2Uy
   fix:
     Rotate the key in the Supabase dashboard, then move any code
     that needs it into an Edge Function or server route.

 INFO  Supabase anon key detected
   Public by design. Not a leak on its own.`;

const FINDS = [
  {
    index: "i",
    title: "Secrets in your shipped JavaScript",
    body: "Supabase service_role keys that bypass RLS entirely, Stripe live keys, AWS credentials, OpenAI and Anthropic tokens, database URIs with passwords. Plus public source maps and readable /.env and /.git paths.",
  },
  {
    index: "ii",
    title: "Misconfiguration",
    body: "Missing or weakened CSP, absent HSTS, clickjacking exposure, cookies without Secure or HttpOnly, CORS that reflects any origin with credentials, outdated TLS, expiring certificates.",
  },
  {
    index: "iii",
    title: "Forgotten infrastructure",
    body: "Certificate transparency logs mined for the staging and admin subdomains you shipped once and forgot. Plus SPF, DKIM and DMARC gaps that let anyone send mail as your domain.",
  },
];

const FAQ = [
  {
    q: "Do I need an account?",
    a: <>No. The free scan needs a URL and nothing else.</>,
  },
  {
    q: "How is this different from the other scanners?",
    a: (
      <>
        It is open source and it runs in CI. Most alternatives are closed,
        one-shot URL scanners. If a scan result is going to change how you ship,
        you should be able to read the code behind it.
      </>
    ),
  },
  {
    q: "Lovable already scans my app. Why use this?",
    a: (
      <>
        Lovable&apos;s scanners are good, but running them before you publish is
        optional, and they only ever scan Lovable&apos;s own output. This works
        the same on Bolt, Cursor, Replit, v0, or hand-written code — and it is
        not graded by the same system that wrote the code.
      </>
    ),
  },
  {
    q: "Is the Supabase anon key a security problem?",
    a: (
      <>
        No — it is public by design, and any scanner that flags it as a leak is
        wrong. It only matters if RLS is not enforced behind it, which is a
        separate check. The key that must never reach a browser is{" "}
        <Code>service_role</Code>, because it bypasses RLS entirely.
      </>
    ),
  },
  {
    q: "Will you store my scan results?",
    a: (
      <>
        <p>
          For 30 days, then they are deleted automatically. That applies to
          every scan, including one somebody else ran against your app — anyone
          can paste any URL into the box above, and we would rather say so than
          let you assume otherwise.
        </p>
        <p className="mt-3">
          Secrets are redacted before anything is written down, so what is kept
          is a report, not a set of working keys. We do not contact the owners
          of scanned apps, and we do not sell scan data. If you want a result
          gone sooner than 30 days, ask and it will be.
        </p>
      </>
    ),
  },
  {
    q: "What if it is wrong?",
    a: (
      <>
        Open an issue. False positives are treated as bugs, not noise — a
        scanner people stop trusting is a scanner that failed.
      </>
    ),
  },
];

export default function HomePage() {
  return (
    <div>
      {/* Hero. Large serif at a narrow measure: the tagline is the one thing on
          the page that should read as a statement rather than documentation. */}
      <section className="pt-14 pb-16 sm:pt-20 sm:pb-20">
        <Shell>
          {/* Tagline fixed in marketing/01-naming.md §1. The "on every deploy"
              half is load-bearing: it carries the continuous/CI position that
              the 04-landing-page.md H1 left to the subheading. */}
          <h1 className="max-w-[46rem] text-[2.6rem] leading-[1.05] font-medium tracking-[-0.02em] text-balance sm:text-[3.9rem]">
            Find out what your app shows the public
            <span className="text-flag"> — on every deploy.</span>
          </h1>

          <p className="mt-7 max-w-[35rem] text-[1.15rem] leading-[1.6] text-ink-soft">
            Open-source security scanner for AI-built web apps. Paste a URL, or
            run it in CI on every deploy. High-confidence detection only — it
            will not waste your time.
          </p>

          <div className="mt-12 grid gap-10 lg:grid-cols-2 lg:gap-14">
            {/* min-w-0 on both tracks: without it the grid sizes to the command
                block's min-content and the whole page overflows on mobile. */}
            <div className="min-w-0">
              <p className="label mb-3 text-faint">Scan a URL</p>
              <ScanForm autoFocus />
            </div>

            <div className="min-w-0">
              <p className="label mb-3 text-faint">Or run it locally</p>
              <CommandBlock
                lines={[
                  `pip install ${BRAND.cmd}`,
                  `${BRAND.cmd} https://myapp.com --fail-on high`,
                ]}
              />
              <a
                href={GITHUB_URL}
                className="mt-3 inline-block font-mono text-xs text-ink underline decoration-rule-firm underline-offset-4 transition-colors hover:text-flag"
              >
                View on GitHub ↗
              </a>
              <div className="mt-2">
                <Todo>
                  Repo is not published, so this link 404s. Also gates the PyPI
                  install above.
                </Todo>
              </div>
            </div>
          </div>

          {/* Trust strip: text only, and every claim here is checkable. */}
          <ul className="mt-14 flex flex-wrap gap-x-6 gap-y-2 border-t border-rule pt-4 font-mono text-xs text-mute">
            <li>{BRAND.license}</li>
            <li>No account required</li>
            <li>Passive by default</li>
            <li>Never scans apps you do not own</li>
          </ul>
        </Shell>
      </section>

      {/* Real output, presented as a plate in a paper rather than a hero
          screenshot. */}
      <section className="border-t border-rule py-14">
        <Shell>
          <Figure
            index="1"
            caption="Actual output, scanning the deliberately vulnerable test app included in the repo. You can reproduce it before trusting this on anything real."
          >
            <div className="bg-plate">
              <div className="flex gap-2 border-b border-mute/25 px-4 py-2.5 font-mono text-xs text-faint">
                <span className="text-flag">$</span>
                {BRAND.cmd} http://localhost:8000 --no-footprint
              </div>
              <pre className="overflow-x-auto px-4 py-4 font-mono text-xs leading-[1.75] text-paper">
                {TERMINAL_OUTPUT}
              </pre>
            </div>
          </Figure>
        </Shell>
      </section>

      <Section index="01" id="checks" title="What it finds">
        <div className="max-w-[36rem] divide-y divide-rule border-t border-rule">
          {FINDS.map((group) => (
            <div
              key={group.title}
              className="py-5 sm:grid sm:grid-cols-[2.5rem_1fr]"
            >
              <p className="label pt-1.5 text-faint">{group.index}</p>
              <div>
                <h3 className="text-[1.05rem] font-medium text-ink">
                  {group.title}
                </h3>
                <p className="mt-1.5 text-[0.95rem] leading-[1.65] text-ink-soft">
                  {group.body}
                </p>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section index="02" title="A scan you run once is a scan you stop running.">
        <Note>
          Exit code 1 on findings at or above your threshold. JSON output for
          anything else you want to do with it.
        </Note>
        <Prose>
          <p>
            Most scanners in this category are a one-time moment: paste a URL,
            get a score, forget about it. Your app changes every deploy. So does
            its public surface.
          </p>
        </Prose>
        <div className="mt-7 max-w-[36rem]">
          <Figure index="2" caption="The whole CI integration.">
            <pre className="overflow-x-auto bg-plate p-4 font-mono text-[0.8rem] leading-[1.8] text-paper">
{`name: security
on: [push]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - run: pip install ${BRAND.cmd}
      - run: ${BRAND.cmd} https://myapp.com --fail-on high`}
            </pre>
          </Figure>
        </div>
      </Section>

      <Section
        index="03"
        id="calibration"
        title={
          <>
            Every other scanner tells you how many checks it runs. We tell you
            how often we are <em className="text-flag">wrong</em>.
          </>
        }
      >
        <Prose>
          <p>
            A security scanner that cries wolf gets ignored, and an ignored
            scanner is worth nothing.
          </p>
          <p>
            So nothing here is flagged on entropy. Minified bundles are full of
            build hashes, SRI digests and UUIDs that look exactly like leaked
            secrets — every pattern we ship is anchored on a vendor prefix or an
            unambiguous structure instead.
          </p>
          <p>
            The clearest example: a Supabase anon key and a{" "}
            <Code>service_role</Code> key are both JWTs with the same shape. We
            decode the role claim rather than pattern-matching, so we never flag
            the anon key — which is public by design and not a leak. Most
            scanners get this wrong.
          </p>
          <p>
            The false-positive rate will be published with the methodology and
            the sample set.
          </p>
        </Prose>
        <Link
          href="/methodology"
          className="label mt-7 inline-block bg-ink px-5 py-3 text-paper transition-colors hover:bg-flag"
        >
          Read the methodology →
        </Link>
        <div className="mt-4 max-w-[36rem]">
          <Todo>
            The rate itself is not measured yet — that is M4 calibration. No
            number can appear here or on the methodology page until it is, and
            the sentence above must not become a claim before then.
          </Todo>
        </div>
      </Section>

      <Section index="04" id="limits" title="What this scanner cannot tell you">
        <Note>
          We would rather tell you where the edges are than sell you a number
          that does not mean what you think it means.
        </Note>
        <Prose>
          <p>
            Passive scanning cannot prove your Row Level Security is actually
            enforced. That needs a live read against your database. The report
            says so explicitly instead of showing you a green check and letting
            you assume you are fine.
          </p>
          <p>
            It also cannot see route-level code loaded lazily at runtime, or
            anything behind a login.
          </p>
        </Prose>
      </Section>

      <Section index="05" title="Is it OK to scan an app I do not own?">
        <Prose>
          <p>
            The passive checks fetch only what the server already sends to every
            visitor — the same requests your browser makes when you load the
            page. No writes, no login attempts, no enumeration, no credential
            that was not already public.
          </p>
          <p>
            Anything deeper requires the owner&apos;s written authorisation, and
            the tool will not do it without.
          </p>
          <p>
            One thing we ask:{" "}
            <strong className="font-medium text-ink">
              do not scan someone&apos;s app and then contact them to sell them
              something.
            </strong>{" "}
            Unsolicited &ldquo;I found a vulnerability in your site&rdquo; is
            extortion-shaped no matter how good your intentions are. If you find
            something real by accident, tell them privately and give them time.
          </p>
        </Prose>
        <Link
          href="/acceptable-use"
          className="label mt-7 inline-block bg-ink px-5 py-3 text-paper transition-colors hover:bg-flag"
        >
          Read the acceptable use policy →
        </Link>
      </Section>

      <Section index="06" title="You can read every check that produced your score.">
        <Prose>
          <p>
            This whole scanner is {BRAND.license} on GitHub. There is a
            deliberately vulnerable test app in the repo — run the scanner
            against it and see exactly what gets caught and what gets missed
            before you trust it on anything real.
          </p>
          <p>Scanning is free forever. That is not a trial.</p>
        </Prose>
        <a
          href={GITHUB_URL}
          className="label mt-7 inline-block bg-ink px-5 py-3 text-paper transition-colors hover:bg-flag"
        >
          View on GitHub ↗
        </a>
      </Section>

      <Section index="07" title="When a customer asks for a security review">
        <Prose>
          <p>
            Finding problems is the free part. {BRAND.name} Cloud is for what
            comes next: history that shows what regressed between deploys, fixes
            written against your actual schema rather than generic advice, and a
            verifiable badge you can put in front of a customer who is asking
            whether you are safe to buy from.
          </p>
        </Prose>
        <div className="mt-5 max-w-[36rem]">
          <Todo>
            Needs an email capture that actually stores the address. Not built —
            per the spec, do not fake a checkout or a signup.
          </Todo>
        </div>
      </Section>

      <Section index="08" title="Questions">
        <div className="max-w-[36rem] divide-y divide-rule border-t border-rule">
          {FAQ.map((item) => (
            <details key={item.q} className="group py-4">
              <summary className="flex cursor-pointer list-none items-baseline justify-between gap-4 [&::-webkit-details-marker]:hidden">
                <h3 className="text-[1.02rem] font-medium text-ink transition-colors group-hover:text-flag">
                  {item.q}
                </h3>
                <span className="label shrink-0 text-faint transition-colors group-open:text-flag">
                  <span className="group-open:hidden">+</span>
                  <span className="hidden group-open:inline">&minus;</span>
                </span>
              </summary>
              <div className="mt-2.5 text-[0.95rem] leading-[1.65] text-ink-soft">
                {item.a}
              </div>
            </details>
          ))}
        </div>
      </Section>

      <section className="border-t border-rule py-12">
        <Shell>
          <p className="label text-faint">Platform guides</p>
          <ul className="mt-3 flex flex-wrap gap-x-6 gap-y-2">
            {PLATFORMS.map((platform) => (
              <li key={platform.slug}>
                <Link
                  href={`/p/${platform.slug}`}
                  className="font-mono text-xs text-ink underline decoration-rule-firm underline-offset-4 transition-colors hover:text-flag"
                >
                  {platform.name}
                </Link>
              </li>
            ))}
          </ul>
        </Shell>
      </section>
    </div>
  );
}
