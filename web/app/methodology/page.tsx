import type { Metadata } from "next";
import Link from "next/link";
import { Code, Note, Prose, Section, Shell } from "@/components/Paper";
import { Todo } from "@/components/Todo";
import { BRAND, GITHUB_URL } from "@/lib/brand";
import {
  GRADE_THRESHOLDS,
  METHODOLOGY_SECTIONS as S,
  SEVERITY_LEVELS,
  VENDOR_PREFIXES,
} from "@/lib/docs";

export const metadata: Metadata = {
  title: "Methodology",
  description:
    "How Overshare decides something is worth reporting, what it deliberately will not report, and where it is blind. No entropy scoring, no machine learning — every pattern is structurally provable or anchored on a vendor prefix.",
  alternates: { canonical: "/methodology" },
  openGraph: {
    title: `Methodology | ${BRAND.name}`,
    description:
      "Every finding is structurally provable or anchored on a vendor-specific prefix. Nothing is reported because it looks suspicious.",
    url: "/methodology",
  },
};

export default function MethodologyPage() {
  return (
    <div>
      <section className="pt-14 pb-12 sm:pt-20">
        <Shell>
          <p className="label text-flag">Methodology</p>
          <h1 className="mt-4 max-w-[38rem] text-[2.4rem] leading-[1.08] font-medium tracking-[-0.02em] text-balance sm:text-[3.2rem]">
            How we decide something is worth reporting.
          </h1>
          <div className="mt-7 max-w-[36rem] space-y-4 text-[1.15rem] leading-[1.6] text-ink-soft">
            <p>
              What {BRAND.name} reports, what it deliberately will not report,
              and where it is blind.
            </p>
            <p className="text-[1.0625rem] text-mute">
              This document exists because a scanner&apos;s check count tells you
              nothing. Any tool can claim 150 checks. The question that matters
              is how often it is wrong, and in which direction.
            </p>
          </div>
        </Shell>
      </section>

      <Section index="01" id="the-one-rule" title={S[0]}>
        <Note>
          Precision over recall. Stated up front, so you can decide whether that
          is the trade you want.
        </Note>
        <div className="mb-6 max-w-[36rem] border-l-2 border-flag bg-flag-wash px-4 py-3 text-[1.05rem] leading-[1.55] font-medium text-flag">
          Every finding is structurally provable or anchored on a vendor-specific
          prefix. Nothing is reported because it looks suspicious.
        </div>
        <Prose>
          <p>
            There is no entropy scoring, no &ldquo;high-randomness
            string&rdquo; detection, no machine-learning classifier. If a pattern
            cannot be made provable, it does not ship.
          </p>
          <p>
            The scanner reads minified production JavaScript, and that code is
            saturated with high-entropy strings that are not secrets: webpack
            chunk hashes, subresource integrity digests, mangled identifiers,
            base64-encoded source maps, inlined font and image data,
            cache-busting fingerprints, UUIDs.
          </p>
          <p>
            An entropy threshold cannot separate those from a real credential,
            because on the axis it measures they are identical. Every
            entropy-based scanner therefore picks a point on a tradeoff: flag
            more real secrets and drown you in noise, or flag fewer and miss
            things. We reject the tradeoff by refusing to guess.
          </p>
          <p>
            The cost is real and we accept it:{" "}
            <strong className="font-medium text-ink">
              {BRAND.name} has false negatives.
            </strong>{" "}
            A credential in a format we do not recognise will be missed. That is
            the deliberate direction of the error, because the failure modes are
            not symmetrical. A missed finding leaves you exactly where you
            already were. A false finding sends you to rotate a production key at
            11pm for no reason, and after that you do not believe the tool again
            — including the time it is right.
          </p>
        </Prose>
      </Section>

      <Section index="02" id="provable" title={S[1]}>
        <Prose>
          <p>Two things qualify.</p>
          <p>
            <strong className="font-medium text-ink">
              A vendor-specific prefix.
            </strong>{" "}
            {VENDOR_PREFIXES.map((prefix, index) => (
              <span key={prefix}>
                <Code>{prefix}</Code>
                {index < VENDOR_PREFIXES.length - 1 ? ", " : ". "}
              </span>
            ))}
            These are namespaces the vendor controls and does not issue for
            anything else. Matching one is not an inference about randomness; it
            is reading a label the vendor wrote.
          </p>
          <p>
            <strong className="font-medium text-ink">
              Decodable structure.
            </strong>{" "}
            Where a credential is a structured document, we parse it and read the
            claim rather than guessing from the surrounding code.
          </p>
          <p>
            The clearest case is Supabase. The anon key and the{" "}
            <Code>service_role</Code> key are both JWTs. They are the same
            length, the same shape, and appear in the same position in the same
            client call. Regex cannot tell them apart, and the difference is the
            entire finding: the anon key is <em>designed</em> to ship to the
            browser, while <Code>service_role</Code> bypasses Row Level Security
            completely.
          </p>
          <p>So we decode the payload and read the role claim:</p>
        </Prose>

        <dl className="mt-5 max-w-[36rem] border-t border-rule">
          <div className="flex flex-col gap-1 border-b border-rule py-3 sm:flex-row sm:gap-4">
            <dt className="shrink-0 font-mono text-xs text-ink sm:w-52">
              role: &quot;anon&quot;
            </dt>
            <dd className="text-[0.95rem] leading-[1.6] text-ink-soft">
              <span className="label mr-2 text-faint">info</span>
              Normal and correct. Flagging it as a leak would be the single most
              common false positive in the category, and several tools do exactly
              that.
            </dd>
          </div>
          <div className="flex flex-col gap-1 border-b border-rule py-3 sm:flex-row sm:gap-4">
            <dt className="shrink-0 font-mono text-xs text-ink sm:w-52">
              role: &quot;service_role&quot;
            </dt>
            <dd className="text-[0.95rem] leading-[1.6] text-ink-soft">
              <span className="label mr-2 text-flag">critical</span>
              Not a guess. The token says what it is.
            </dd>
          </div>
        </dl>

        <Prose className="mt-6">
          <p>
            The same principle covers database connection strings (parsed for an
            embedded password rather than matched loosely) and private key blocks
            (matched on the PEM armour, not on entropy).
          </p>
        </Prose>
      </Section>

      <Section index="03" id="severity" title={S[2]}>
        <Note>
          Severity is a property of the check, not of how alarming the string
          looks.
        </Note>

        <div className="max-w-[36rem] border-t border-rule">
          {SEVERITY_LEVELS.map((level) => (
            <div key={level.level} className="border-b border-rule py-4">
              <div className="flex items-baseline justify-between gap-4">
                <h3 className="label text-ink">{level.level}</h3>
                <p className="font-mono text-xs text-mute">
                  <span className="text-faint">penalty </span>
                  <span className="tabular-nums text-ink">
                    &minus;{level.penalty}
                  </span>
                </p>
              </div>
              <p className="mt-2 text-[0.95rem] leading-[1.6] text-ink-soft">
                {level.meaning}
              </p>
              <p className="mt-1 font-mono text-xs text-mute">{level.example}</p>
            </div>
          ))}
        </div>

        <h3 className="mt-8 text-[1.2rem] font-medium">Scoring</h3>
        <Prose className="mt-3">
          <p>
            Score is <Code>100 − total penalty</Code>, floored at zero. Grades:{" "}
            {GRADE_THRESHOLDS.map((entry) => (
              <span key={entry.grade}>
                <strong className="font-medium text-ink">{entry.grade}</strong>{" "}
                <span className="font-mono text-sm tabular-nums">
                  ≥ {entry.min}
                </span>
                ,{" "}
              </span>
            ))}
            otherwise <strong className="font-medium text-ink">F</strong>.
          </p>
          <p>
            <strong className="font-medium text-ink">
              Penalties apply once per check, not once per occurrence.
            </strong>{" "}
            One leaked Stripe key found in three different bundles is one key to
            rotate, not three problems, and scoring it three times would say
            something false about how much work you have to do. It would also
            mean a site that ships the same bundle under four filenames scores
            worse than an identical site that ships one — which is a fact about
            their build tool, not their security.
          </p>
        </Prose>
      </Section>

      <Section index="04" id="what-it-does-not-do" title={S[3]}>
        <Prose>
          <p>
            {BRAND.name} only looks at what your app already serves to anybody
            who visits it.
          </p>
        </Prose>

        <ul className="mt-5 max-w-[36rem] border-t border-rule">
          {[
            [
              "It does not log in.",
              "No credentials, no authenticated crawling.",
            ],
            [
              "It does not write.",
              "No POST, PUT, PATCH or DELETE to your app, ever.",
            ],
            [
              "It does not enumerate.",
              "No directory brute-forcing, no parameter fuzzing, no user enumeration.",
            ],
            [
              "It does not exploit.",
              "Where a weakness is detected, it is detected from a response, not by demonstrating impact.",
            ],
            [
              "It does not use the credentials it finds.",
              "A discovered service_role key is reported and redacted; it is never used to connect to anything. Proving it works would be unauthorised access to your database.",
            ],
          ].map(([rule, detail]) => (
            <li
              key={rule}
              className="border-b border-rule py-3 text-[0.95rem] leading-[1.6] text-ink-soft"
            >
              <strong className="font-medium text-ink">{rule}</strong> {detail}
            </li>
          ))}
        </ul>

        <Prose className="mt-6">
          <p>
            Every secret is redacted before it reaches a report, a log, or the
            database: enough characters to recognise which key it is, never
            enough to use it.
          </p>
        </Prose>
      </Section>

      <Section index="05" id="blind-spots" title={S[4]}>
        <Note>
          A scanner that only advertises what it catches is telling you half of
          what you need.
        </Note>

        <ul className="max-w-[36rem] border-t border-rule">
          {[
            [
              "Credentials in unrecognised formats.",
              "Self-issued tokens, internal API keys, and any vendor whose prefix we have not implemented.",
            ],
            [
              "Anything behind a login.",
              "The entire authenticated surface is invisible. Most real business logic lives there.",
            ],
            [
              "Runtime-only behaviour.",
              "We fetch and parse without executing JavaScript, so a key assembled at runtime from fragments, or fetched from a config endpoint after load, is not seen.",
            ],
            [
              "Row Level Security enforcement.",
              "We detect that a Supabase project is in use and report that RLS was not tested. Detecting a misconfigured policy requires actually querying the database, which is Tier B and needs your authorisation. Until then this is a blind spot, and the report says so rather than implying a clean bill.",
            ],
            [
              "Server-side vulnerabilities.",
              "Injection, broken access control, insecure deserialisation. None of it is visible from outside.",
            ],
            [
              "Whether a finding matters to you.",
              "We can prove a key is published. We cannot know it is a test key in a sandbox account.",
            ],
          ].map(([spot, detail]) => (
            <li
              key={spot}
              className="border-b border-rule py-3 text-[0.95rem] leading-[1.6] text-ink-soft"
            >
              <strong className="font-medium text-ink">{spot}</strong> {detail}
            </li>
          ))}
        </ul>

        <p className="mt-6 max-w-[36rem] border-l-2 border-rule-firm bg-inset px-4 py-3 text-[0.95rem] leading-[1.6] text-ink">
          A clean {BRAND.name} report means the public surface we know how to
          check looks right. It does not mean the app is secure, and the report
          says that in those words.
        </p>
      </Section>

      <Section index="06" id="false-positive-rate" title={S[5]}>
        <div className="max-w-[36rem] border-l-2 border-flag bg-flag-wash px-4 py-3.5">
          <p className="label text-flag">Not yet measured</p>
          <p className="mt-2 text-[0.95rem] leading-[1.65] text-flag">
            This section is deliberately empty rather than filled with an
            estimate. The calibration run — every finding across 20–30 real
            applications verified by hand, and every false positive fixed or the
            pattern withdrawn — has not been done. When it has, the rate, the
            sample, the date and the method go here, along with the raw results.
          </p>
          <p className="mt-2.5 text-[0.95rem] leading-[1.65] text-flag">
            Publishing a number we have not measured would defeat the purpose of
            the document that publishes it.
          </p>
        </div>

        <Prose className="mt-6">
          <p>
            What exists today is the design property, not the measurement. The
            test suite includes a bundle of benign lookalikes — build hashes, SRI
            digests, example keys from vendor documentation, anon JWTs — and{" "}
            <Code>test_benign_bundle_produces_no_findings</Code> asserts that it
            produces <strong className="font-medium text-ink">zero</strong>{" "}
            findings. Every new pattern must add its own benign lookalike to that
            bundle before it can ship.
          </p>
          <p>
            That is a floor, not a false-positive rate. It proves the patterns do
            not fire on the lookalikes we thought of.
          </p>
        </Prose>
      </Section>

      <Section index="07" id="report-a-false-positive" title={S[6]}>
        <Prose>
          <p>
            A false positive is a bug of the highest severity in this project,
            and it is treated as one.
          </p>
          <p>
            Open an issue with the <Code>false-positive</Code> label. Include the{" "}
            <Code>check_id</Code>, and the surrounding context if you can share
            it.
          </p>
          <p>
            <strong className="font-medium text-ink">
              Do not include the actual credential.
            </strong>{" "}
            The redacted evidence string from the report is what we need, and if
            it turns out we need more we will ask.
          </p>
          <p>
            If a finding on a large real production site cannot be reproduced as
            a genuine issue, the working assumption is that the pattern is wrong
            — not that the site is unusual.
          </p>
        </Prose>
        <a
          href={`${GITHUB_URL}/issues`}
          className="label mt-6 inline-block bg-ink px-5 py-3 text-paper transition-colors hover:bg-flag"
        >
          Open an issue ↗
        </a>
        <div className="mt-3">
          <Todo>Repo is not published, so this link 404s.</Todo>
        </div>
      </Section>

      <Section index="08" id="reproducing" title={S[7]}>
        <Prose>
          <p>
            Detection lives in <Code>overshare/checks/</Code>. There is no hosted
            component involved in deciding what is a finding; the CLI and the
            hosted scan run the same code, so anything here can be verified
            against the source.
          </p>
          <p>
            Check identifiers are stable and are never renamed once shipped,
            because scan-to-scan comparison keys off them.
          </p>
        </Prose>
        <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2">
          <Link
            href="/acceptable-use"
            className="font-mono text-xs text-ink underline decoration-rule-firm underline-offset-4 transition-colors hover:text-flag"
          >
            Acceptable use →
          </Link>
          <Link
            href="/"
            className="font-mono text-xs text-ink underline decoration-rule-firm underline-offset-4 transition-colors hover:text-flag"
          >
            Scan an app →
          </Link>
        </div>
      </Section>
    </div>
  );
}
