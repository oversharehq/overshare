import Link from "next/link";
import { ScanForm } from "@/components/ScanForm";
import { PLATFORMS } from "@/lib/platforms";

const CHECK_GROUPS = [
  {
    title: "Secrets in your bundle",
    body: "Everything your app ships to the browser is public, including the parts you assumed were hidden by minification.",
    items: [
      "Supabase service_role keys, which bypass Row Level Security entirely",
      "Stripe, Paddle and LemonSqueezy secret keys",
      "Cloud and provider credentials with recognisable prefixes",
      "Source maps that rebuild your original code",
      "Exposed .env and .git paths",
    ],
  },
  {
    title: "Platform and transport",
    body: "How your app is built determines what can go wrong with it, so we fingerprint the stack before deciding what to check.",
    items: [
      "Backend detection: Supabase, Firebase, Convex, PocketBase",
      "Builder and framework fingerprinting",
      "Security headers: CSP, HSTS, frame and content-type options",
      "TLS version, certificate validity, mixed content",
      "CORS configuration that lets other sites read your data",
    ],
  },
  {
    title: "External footprint",
    body: "The parts of your setup that are public but easy to forget about.",
    items: [
      "DNS records and mail authentication (SPF, DKIM, DMARC)",
      "Certificate transparency logs, which reveal forgotten staging and admin subdomains",
      "Historical snapshots that may still expose old configuration",
    ],
  },
];

export default function HomePage() {
  return (
    <div className="mx-auto max-w-5xl px-6">
      <section className="py-16 sm:py-24">
        <p className="text-sm font-medium text-slate-500">
          Security scanning for AI-built apps
        </p>
        <h1 className="mt-3 max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Prove your app is safe to buy
        </h1>
        <p className="mt-5 max-w-2xl text-lg text-slate-600">
          Customers ask about security before they sign. LeakScan checks what your
          app already shows the public — exposed API keys, leaked source maps,
          missing protections — and gives you a report you can hand over.
        </p>

        <div className="mt-8 max-w-2xl">
          <ScanForm autoFocus />
        </div>

        <p className="mt-10 text-sm text-slate-500">
          Built for apps made with{" "}
          {PLATFORMS.map((platform, index) => (
            <span key={platform.slug}>
              <Link
                href={`/p/${platform.slug}`}
                className="font-medium text-slate-700 underline underline-offset-4 hover:text-slate-900"
              >
                {platform.name}
              </Link>
              {index < PLATFORMS.length - 1 ? ", " : "."}
            </span>
          ))}
        </p>
      </section>

      <section id="checks" className="scroll-mt-6 border-t border-slate-200 py-16">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          What we check
        </h2>
        <p className="mt-3 max-w-2xl text-slate-600">
          Every check runs against what your app serves to any visitor. Nothing
          here requires a login or a credential you have not already published.
        </p>

        <div className="mt-10 grid gap-8 sm:grid-cols-3">
          {CHECK_GROUPS.map((group) => (
            <div key={group.title}>
              <h3 className="text-sm font-semibold text-slate-900">
                {group.title}
              </h3>
              <p className="mt-2 text-sm text-slate-600">{group.body}</p>
              <ul className="mt-4 space-y-2">
                {group.items.map((item) => (
                  <li key={item} className="flex gap-2 text-sm text-slate-600">
                    <span
                      className="mt-2 h-1 w-1 shrink-0 rounded-full bg-slate-300"
                      aria-hidden
                    />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-slate-200 py-16">
        <div className="grid gap-10 sm:grid-cols-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              We report what we can prove
            </h2>
            <p className="mt-3 text-slate-600">
              A scanner that cries wolf is worse than no scanner. LeakScan reports
              a secret only when the key structurally identifies itself — a known
              vendor prefix, or a token we can decode and read. We do not guess
              from how random a string looks, because minified bundles are full of
              build hashes that look exactly like secrets.
            </p>
            <p className="mt-3 text-slate-600">
              The tradeoff is deliberate, so every report states plainly what it
              did not check. A clean result is never dressed up as a clean bill of
              health.
            </p>
          </div>

          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              How this stays above board
            </h2>
            <p className="mt-3 text-slate-600">
              LeakScan makes the same requests any visitor&apos;s browser makes. It
              never attempts a login, never modifies data, and never uses a
              credential that was not already being handed to every visitor.
            </p>
            <p className="mt-3 text-slate-600">
              Deeper testing — anything touching authenticated surface — runs only
              on apps whose owner has asked for it in writing.
            </p>
          </div>
        </div>
      </section>

      <section className="border-t border-slate-200 py-16">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Scan your app
        </h2>
        <p className="mt-3 max-w-2xl text-slate-600">
          No signup, no card. Paste the URL and read the report.
        </p>
        <div className="mt-6 max-w-2xl">
          <ScanForm />
        </div>
      </section>
    </div>
  );
}
