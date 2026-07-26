import type { Metadata } from "next";
import { IBM_Plex_Mono, Newsreader } from "next/font/google";
import Link from "next/link";
import { Mark } from "@/components/Mark";
import { BRAND, GITHUB_URL } from "@/lib/brand";
import "./globals.css";

const newsreader = Newsreader({
  subsets: ["latin"],
  style: ["normal", "italic"],
  axes: ["opsz"],
  variable: "--font-newsreader",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plex-mono",
});

// Production is https://oversharehq.com. Kept configurable so preview
// deployments emit their own canonical URLs rather than the production one.
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: `${BRAND.name} — open-source security scanner for AI-built apps`,
    template: `%s | ${BRAND.name}`,
  },
  description:
    "Open-source security scanner for AI-built web apps. Paste a URL or run it in CI on every deploy. Finds exposed API keys, source maps and misconfiguration — high-confidence detection only.",
  openGraph: {
    type: "website",
    siteName: BRAND.name,
    url: siteUrl,
  },
  robots: { index: true, follow: true },
};

const NAV = [
  { href: "/#checks", index: "01", label: "What it finds" },
  { href: "/#calibration", index: "03", label: "Calibration" },
  { href: "/#limits", index: "04", label: "Limits" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`h-full antialiased ${newsreader.variable} ${plexMono.variable}`}
    >
      <body className="flex min-h-full flex-col font-serif text-ink">
        {/* Masthead. The heavy-over-hairline rule pair is the one piece of
            deliberate ornament on the page — it reads as a printed banner. */}
        <header className="print-hidden border-t-2 border-ink">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex items-center justify-between gap-6 border-b border-rule py-4">
              <Link href="/" className="group flex items-center gap-2.5">
                <Mark />
                <span className="text-[1.35rem] leading-none font-medium tracking-tight text-ink">
                  {BRAND.name}
                </span>
              </Link>

              <nav className="flex items-center gap-5 sm:gap-7">
                {NAV.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="label hidden text-mute transition-colors hover:text-flag sm:inline"
                  >
                    <span className="text-faint">{item.index}</span>{" "}
                    {item.label}
                  </Link>
                ))}
                <a
                  href={GITHUB_URL}
                  className="label text-ink transition-colors hover:text-flag"
                >
                  GitHub&nbsp;↗
                </a>
              </nav>
            </div>
          </div>
        </header>

        <main className="flex-1">{children}</main>

        {/* Colophon. Set narrow and in mono, the way a document records its own
            terms rather than the way a site sells them. */}
        <footer className="print-hidden mt-28 border-t border-rule">
          <div className="mx-auto max-w-6xl px-6 py-12">
            <div className="grid gap-10 sm:grid-cols-[1fr_auto] sm:gap-16">
              <div className="max-w-xl">
                <p className="label text-faint">Scope</p>
                <p className="mt-3 text-[0.95rem] leading-relaxed text-ink-soft">
                  {BRAND.name} only requests what an app already serves to any
                  visitor. It does not attempt logins, does not modify data, and
                  does not use credentials that were not already public.
                </p>
                <p className="mt-3 font-mono text-xs leading-relaxed text-mute">
                  Only scan applications you own or have written permission to
                  test.
                </p>
              </div>

              <div className="sm:text-right">
                <p className="label text-faint">Terms</p>
                <ul className="mt-3 space-y-1.5 font-mono text-xs">
                  <li>
                    <Link
                      href="/methodology"
                      className="text-ink underline decoration-rule-firm underline-offset-4 transition-colors hover:text-flag"
                    >
                      Methodology
                    </Link>
                  </li>
                  <li>
                    <Link
                      href="/acceptable-use"
                      className="text-ink underline decoration-rule-firm underline-offset-4 transition-colors hover:text-flag"
                    >
                      Acceptable use
                    </Link>
                  </li>
                  <li>
                    <a
                      href={GITHUB_URL}
                      className="text-ink underline decoration-rule-firm underline-offset-4 transition-colors hover:text-flag"
                    >
                      Source on GitHub ↗
                    </a>
                  </li>
                  <li className="text-mute">{BRAND.license}</li>
                </ul>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
