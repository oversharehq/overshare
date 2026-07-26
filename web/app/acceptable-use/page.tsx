import type { Metadata } from "next";
import Link from "next/link";
import { Code, Note, Prose, Section, Shell } from "@/components/Paper";
import { BRAND } from "@/lib/brand";
import {
  ACCEPTABLE_USE_SECTIONS as S,
  RETENTION_DAYS,
  SCAN_TIERS,
} from "@/lib/docs";

export const metadata: Metadata = {
  title: "Acceptable use",
  description:
    "Scan applications you own, or that you have written permission to test. What the passive scan does, what each tier requires, what is prohibited, and what happens to scans submitted to the hosted service.",
  alternates: { canonical: "/acceptable-use" },
  openGraph: {
    title: `Acceptable use | ${BRAND.name}`,
    description:
      "Scan applications you own, or that you have written permission to test. Nothing else.",
    url: "/acceptable-use",
  },
};

const PROHIBITED = [
  [
    "Scanning an application you neither own nor have permission to test",
    "beyond a passive scan, at any tier.",
  ],
  [
    "Using Overshare as reconnaissance for an attack.",
    "Establishing what an application exposes in order to exploit it is unauthorised access, and the scan is evidence of intent.",
  ],
  [
    "Scan-then-pitch.",
    "Running a scan against someone else's application and contacting them to sell a fix reads as extortion regardless of how it was meant, and creates a written record of profiting from an unsolicited scan. We will not do this, and you may not do it with output from this tool.",
  ],
  [
    "Publishing findings about a third party's application",
    "without giving them private notice and reasonable time to fix it.",
  ],
  [
    "Using a discovered credential.",
    "A key found in a bundle is reported and redacted. Connecting to anything with it is unauthorised access to a system, and the fact that the key was carelessly published is not a defence.",
  ],
  [
    "Volumetric use.",
    "Automating Overshare to sweep large numbers of third-party applications. The rate limits are not the policy; this is.",
  ],
];

export default function AcceptableUsePage() {
  return (
    <div>
      <section className="pt-14 pb-12 sm:pt-20">
        <Shell>
          <p className="label text-flag">Acceptable use</p>
          <h1 className="mt-4 max-w-[38rem] text-[2.4rem] leading-[1.08] font-medium tracking-[-0.02em] text-balance sm:text-[3.2rem]">
            Scan applications you own.
          </h1>
          <div className="mt-7 max-w-[36rem] space-y-4 text-[1.15rem] leading-[1.6] text-ink-soft">
            <p>
              {BRAND.name} points a scanner at a web application. That is a
              capability that is legitimate when you own the target and a
              criminal offence when you do not, so the boundary matters more than
              it does for most developer tools.
            </p>
            <p className="text-[1.0625rem] text-mute">
              Under Australia&apos;s <strong>Criminal Code Act</strong> and the US{" "}
              <strong>Computer Fraud and Abuse Act</strong>, unauthorised access
              to a computer system is the offence. Good intent is not a defence.
              This applies to you when you run the CLI, and to us when we run a
              scan you submitted.
            </p>
          </div>
        </Shell>
      </section>

      <Section index="01" id="short-version" title={S[0]}>
        <p className="max-w-[36rem] border-l-2 border-flag bg-flag-wash px-4 py-3.5 text-[1.15rem] leading-[1.5] font-medium text-flag">
          Scan applications you own, or that you have written permission to test.
          Nothing else.
        </p>
      </Section>

      <Section index="02" id="default-behaviour" title={S[1]}>
        <Note>
          A passive scan of a public URL is, in itself, ordinary web traffic.
        </Note>
        <Prose>
          <p>
            The default scan — the CLI, the GitHub Action, and the scan box on
            the website — is{" "}
            <strong className="font-medium text-ink">passive</strong>. It requests
            only what the application already serves to any member of the public:
            the page, its JavaScript bundles, its response headers, its TLS
            configuration, public DNS records, and certificate transparency logs.
          </p>
          <p>
            It does not log in, does not send POST/PUT/PATCH/DELETE, does not
            brute-force paths or parameters, and does not use any credential it
            discovers.
          </p>
          <p>
            That is why the default carries no authorisation requirement. It is
            not a licence to point it at anything you like for any purpose — see
            what is prohibited below.
          </p>
        </Prose>
      </Section>

      <Section index="03" id="tiers" title={S[2]}>
        <div className="max-w-[36rem] border-t border-rule">
          {SCAN_TIERS.map((tier) => (
            <div key={tier.tier} className="border-b border-rule py-4">
              <div className="flex items-baseline gap-3">
                <span className="label text-flag">{tier.tier}</span>
                <h3 className="text-[1.05rem] font-medium text-ink">
                  {tier.name}
                </h3>
                {!tier.implemented && (
                  <span className="label text-faint">not implemented yet</span>
                )}
              </div>
              <p className="mt-2 text-[0.95rem] leading-[1.6] text-ink-soft">
                {tier.does}
              </p>
              <p className="mt-2 flex flex-wrap gap-x-2 font-mono text-xs leading-[1.6]">
                <span className="text-faint">Authorisation</span>
                <span
                  className={
                    tier.tier === "C" ? "font-medium text-flag" : "text-ink"
                  }
                >
                  {tier.authorisation}
                </span>
              </p>
            </div>
          ))}
        </div>

        <Prose className="mt-6">
          <p>
            When Tier B arrives, the discipline will be structural rather than
            conventional: single-row reads, rate limited, no writes, no
            enumeration. Prove the door is unlocked; do not walk through it.
          </p>
        </Prose>
      </Section>

      <Section index="04" id="prohibited" title={S[3]}>
        <ul className="max-w-[36rem] border-t border-rule">
          {PROHIBITED.map(([rule, detail]) => (
            <li
              key={rule}
              className="flex gap-3 border-b border-rule py-3 text-[0.95rem] leading-[1.6] text-ink-soft"
            >
              <span className="mt-2 h-2.5 w-[3px] shrink-0 bg-flag" aria-hidden />
              <span>
                <strong className="font-medium text-ink">{rule}</strong> {detail}
              </span>
            </li>
          ))}
          <li className="flex gap-3 border-b border-rule py-3 text-[0.95rem] leading-[1.6] text-ink-soft">
            <span className="mt-2 h-2.5 w-[3px] shrink-0 bg-flag" aria-hidden />
            <span>
              <strong className="font-medium text-ink">
                Circumventing the SSRF protections
              </strong>{" "}
              to reach internal or private-network addresses. The{" "}
              <Code>--unsafe-allow-private-ips</Code> flag exists for scanning
              your own local test app and logs a warning saying so. Using it
              against infrastructure that is not yours is exactly the conduct the
              guard is there to prevent.
            </span>
          </li>
        </ul>
      </Section>

      <Section index="05" id="third-party-findings" title={S[4]}>
        <Prose>
          <p>
            It happens — you scan your own app and a shared dependency, a
            subdomain, or a misconfigured third-party service surfaces.
          </p>
          <p>
            Disclose it privately to the owner, give them time to fix it, and
            publish nothing in the meantime. Do not offer them a paid fix in the
            same message.
          </p>
        </Prose>
      </Section>

      <Section index="06" id="hosted-scans" title={S[5]}>
        <Note>
          Anyone can submit any URL to the public scan box, so a scan of your
          application may exist because someone else submitted it.
        </Note>

        <ul className="max-w-[36rem] border-t border-rule">
          {[
            `Scan results are kept for ${RETENTION_DAYS} days and then deleted automatically.`,
            "Secrets are redacted before a result reaches a report, a log, or the database. Enough characters survive to identify which key it is, never enough to use it.",
            "We do not contact the owners of scanned applications.",
            "We do not sell scan data, and we do not use it to approach anyone commercially.",
          ].map((item) => (
            <li
              key={item}
              className="border-b border-rule py-3 text-[0.95rem] leading-[1.6] text-ink-soft"
            >
              {item}
            </li>
          ))}
        </ul>

        <p className="mt-6 max-w-[36rem] border-l-2 border-rule-firm bg-inset px-4 py-3 text-[0.95rem] leading-[1.6] text-ink">
          That result is a report on your public surface, it expires in{" "}
          {RETENTION_DAYS} days, and if you want it gone sooner, ask.
        </p>
      </Section>

      <Section index="07" id="enforcement" title={S[6]}>
        <Prose>
          <p>
            We can decline or block scans, and we can rate-limit or ban clients.
            We would rather explain a boundary than enforce one, so if your use
            case sits near a line here, ask first.
          </p>
        </Prose>
      </Section>

      <Section index="08" id="questions" title={S[7]}>
        <Prose>
          <p>
            Open an issue for anything that is not itself sensitive. For a
            suspected vulnerability in {BRAND.name} itself, follow the security
            policy in the repository rather than filing it publicly.
          </p>
        </Prose>

        <p className="mt-6 max-w-[36rem] font-mono text-xs leading-[1.7] text-mute">
          This document describes how the project expects its tool to be used. It
          is not legal advice, and it does not override the law in your
          jurisdiction, which may be stricter.
        </p>

        <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2">
          <Link
            href="/methodology"
            className="font-mono text-xs text-ink underline decoration-rule-firm underline-offset-4 transition-colors hover:text-flag"
          >
            Methodology →
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
