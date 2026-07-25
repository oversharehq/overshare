import Link from "next/link";
import { CommandBlock } from "@/components/CommandBlock";
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
    title: "Secrets in your shipped JavaScript",
    body: "Supabase service_role keys that bypass RLS entirely, Stripe live keys, AWS credentials, OpenAI and Anthropic tokens, database URIs with passwords. Plus public source maps and readable /.env and /.git paths.",
  },
  {
    title: "Misconfiguration",
    body: "Missing or weakened CSP, absent HSTS, clickjacking exposure, cookies without Secure or HttpOnly, CORS that reflects any origin with credentials, outdated TLS, expiring certificates.",
  },
  {
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
        <code className="font-mono text-sm">service_role</code>, because it
        bypasses RLS entirely.
      </>
    ),
  },
  {
    q: "Will you store my scan results?",
    a: (
      <>
        <Todo>
          Blocked on the retention decision in build brief §12. The API stores
          every scan in SQLite today, including scans of apps the submitter may
          not own. This question must be answered honestly before launch.
        </Todo>
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
    <div className="mx-auto max-w-5xl px-6">
      {/* Hero */}
      <section className="py-16 sm:py-20">
        {/* Tagline fixed in marketing/01-naming.md §1. The "on every deploy"
            half is load-bearing: it carries the continuous/CI position that the
            04-landing-page.md H1 left to the subheading. */}
        <h1 className="max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Find out what your app shows the public — on every deploy.
        </h1>
        <p className="mt-5 max-w-2xl text-lg text-slate-600">
          Open-source security scanner for AI-built web apps. Paste a URL, or run
          it in CI on every deploy. High-confidence detection only — it will not
          waste your time.
        </p>

        <div className="mt-10 grid gap-8 lg:grid-cols-2">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Scan a URL
            </p>
            <ScanForm autoFocus />
          </div>

          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Or run it locally
            </p>
            <CommandBlock
              lines={[
                `pip install ${BRAND.cmd}`,
                `${BRAND.cmd} https://myapp.com --fail-on high`,
              ]}
            />
            <a
              href={GITHUB_URL}
              className="mt-3 inline-block text-sm font-medium text-slate-700 underline underline-offset-4 hover:text-slate-900"
            >
              View on GitHub →
            </a>
            <div className="mt-2">
              <Todo>
                Repo is not published, so this link 404s. Also gates the PyPI
                install above.
              </Todo>
            </div>
          </div>
        </div>

        <p className="mt-10 text-sm text-slate-500">
          {BRAND.license} · No account required · Passive by default · Never
          scans apps you do not own
        </p>
      </section>

      {/* Real output */}
      <section className="border-t border-slate-200 py-14">
        <div className="overflow-hidden rounded-lg border border-slate-800 bg-slate-900">
          <div className="border-b border-slate-800 px-4 py-2 font-mono text-xs text-slate-400">
            $ {BRAND.cmd} http://localhost:8000 --no-footprint
          </div>
          <pre className="overflow-x-auto px-4 py-4 font-mono text-xs leading-relaxed text-slate-200">
            {TERMINAL_OUTPUT}
          </pre>
        </div>
        <p className="mt-3 text-sm text-slate-500">
          Actual output, scanning the deliberately vulnerable test app included
          in the repo. You can reproduce it before trusting this on anything
          real.
        </p>
      </section>

      {/* What it finds */}
      <section id="checks" className="scroll-mt-6 border-t border-slate-200 py-16">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          What it finds
        </h2>
        <div className="mt-8 grid gap-8 sm:grid-cols-3">
          {FINDS.map((group) => (
            <div key={group.title}>
              <h3 className="text-sm font-semibold text-slate-900">
                {group.title}
              </h3>
              <p className="mt-2 text-sm text-slate-600">{group.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Differentiator */}
      <section className="border-t border-slate-200 py-16">
        <h2 className="max-w-3xl text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
          Every other scanner tells you how many checks it runs. We tell you how
          often we are wrong.
        </h2>
        <div className="mt-6 max-w-2xl space-y-4 text-slate-600">
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
            <code className="font-mono text-sm">service_role</code> key are both
            JWTs with the same shape. We decode the role claim rather than
            pattern-matching, so we never flag the anon key — which is public by
            design and not a leak. Most scanners get this wrong.
          </p>
          <p>
            The false-positive rate will be published with the methodology and
            the sample set.
          </p>
          <Todo>
            Not measured yet — that is M4 calibration. No number can appear here
            until it is, and the sentence above must not become a claim before
            then. METHODOLOGY.md does not exist, so the CTA below has nowhere to
            go.
          </Todo>
        </div>
      </section>

      {/* CI */}
      <section className="border-t border-slate-200 py-16">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          A scan you run once is a scan you stop running.
        </h2>
        <p className="mt-3 max-w-2xl text-slate-600">
          Most scanners in this category are a one-time moment: paste a URL, get
          a score, forget about it. Your app changes every deploy. So does its
          public surface.
        </p>

        <pre className="mt-6 max-w-2xl overflow-x-auto rounded-md border border-slate-800 bg-slate-900 p-4 font-mono text-xs leading-relaxed text-slate-100">
{`name: security
on: [push]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - run: pip install ${BRAND.cmd}
      - run: ${BRAND.cmd} https://myapp.com --fail-on high`}
        </pre>

        <p className="mt-4 max-w-2xl text-slate-600">
          Exit code 1 on findings at or above your threshold. JSON output for
          anything else you want to do with it.
        </p>
      </section>

      {/* Limits */}
      <section className="border-t border-slate-200 py-16">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          What this scanner cannot tell you
        </h2>
        <div className="mt-4 max-w-2xl space-y-4 text-slate-600">
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
          <p>
            We would rather tell you where the edges are than sell you a number
            that does not mean what you think it means.
          </p>
        </div>
      </section>

      {/* Legality */}
      <section className="border-t border-slate-200 py-16">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Is it OK to scan an app I do not own?
        </h2>
        <div className="mt-4 max-w-2xl space-y-4 text-slate-600">
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
            <strong className="font-semibold text-slate-900">
              do not scan someone&apos;s app and then contact them to sell them
              something.
            </strong>{" "}
            Unsolicited &ldquo;I found a vulnerability in your site&rdquo; is
            extortion-shaped no matter how good your intentions are. If you find
            something real by accident, tell them privately and give them time.
          </p>
          <Todo>Acceptable use policy page does not exist yet.</Todo>
        </div>
      </section>

      {/* Open source */}
      <section className="border-t border-slate-200 py-16">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          You can read every check that produced your score.
        </h2>
        <div className="mt-4 max-w-2xl space-y-4 text-slate-600">
          <p>
            This whole scanner is {BRAND.license} on GitHub. There is a
            deliberately vulnerable test app in the repo — run the scanner
            against it and see exactly what gets caught and what gets missed
            before you trust it on anything real.
          </p>
          <p>Scanning is free forever. That is not a trial.</p>
        </div>
        <a
          href={GITHUB_URL}
          className="mt-5 inline-block rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700"
        >
          View on GitHub →
        </a>
      </section>

      {/* Hosted */}
      <section className="border-t border-slate-200 py-16">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          When a customer asks for a security review
        </h2>
        <p className="mt-4 max-w-2xl text-slate-600">
          Finding problems is the free part. {BRAND.name} Cloud is for what comes
          next: history that shows what regressed between deploys, fixes written
          against your actual schema rather than generic advice, and a verifiable
          badge you can put in front of a customer who is asking whether you are
          safe to buy from.
        </p>
        <div className="mt-4">
          <Todo>
            Needs an email capture that actually stores the address. Not built —
            per the spec, do not fake a checkout or a signup.
          </Todo>
        </div>
      </section>

      {/* FAQ */}
      <section className="border-t border-slate-200 py-16">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Questions
        </h2>
        <div className="mt-6 max-w-3xl divide-y divide-slate-200 border-y border-slate-200">
          {FAQ.map((item) => (
            <details key={item.q} className="group py-4">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-sm font-semibold text-slate-900 [&::-webkit-details-marker]:hidden">
                {item.q}
                <svg
                  className="h-4 w-4 shrink-0 text-slate-400 transition-transform group-open:rotate-90"
                  viewBox="0 0 16 16"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  aria-hidden
                >
                  <path d="M6 4l4 4-4 4" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </summary>
              <div className="mt-2 text-sm text-slate-600">{item.a}</div>
            </details>
          ))}
        </div>
      </section>

      {/* Platforms */}
      <section className="border-t border-slate-200 py-12">
        <p className="text-sm text-slate-500">
          Platform guides:{" "}
          {PLATFORMS.map((platform, index) => (
            <span key={platform.slug}>
              <Link
                href={`/p/${platform.slug}`}
                className="font-medium text-slate-700 underline underline-offset-4 hover:text-slate-900"
              >
                {platform.name}
              </Link>
              {index < PLATFORMS.length - 1 ? ", " : ""}
            </span>
          ))}
        </p>
      </section>
    </div>
  );
}
