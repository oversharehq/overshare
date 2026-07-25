import type { Metadata } from "next";
import Link from "next/link";
import { BRAND, GITHUB_URL } from "@/lib/brand";
import "./globals.css";

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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col font-sans">
        <header className="print-hidden border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
            <Link href="/" className="flex items-center gap-2">
              <span className="grid h-7 w-7 place-items-center rounded bg-slate-900 font-mono text-sm font-bold text-white">
                L
              </span>
              <span className="text-base font-semibold tracking-tight text-slate-900">
                {BRAND.name}
              </span>
            </Link>
            <nav className="flex items-center gap-6 text-sm text-slate-600">
              <Link href="/#checks" className="hover:text-slate-900">
                What it finds
              </Link>
              <Link href="/p/lovable" className="hover:text-slate-900">
                Platforms
              </Link>
              <a href={GITHUB_URL} className="hover:text-slate-900">
                GitHub
              </a>
            </nav>
          </div>
        </header>

        <main className="flex-1">{children}</main>

        <footer className="print-hidden mt-24 border-t border-slate-200 bg-white">
          <div className="mx-auto max-w-5xl px-6 py-10 text-sm text-slate-500">
            <p className="max-w-2xl">
              {BRAND.name} only requests what an app already serves to any
              visitor. It does not attempt logins, does not modify data, and does
              not use credentials that were not already public.
            </p>
            <p className="mt-4">
              Only scan applications you own or have written permission to test.
            </p>
            <p className="mt-4">
              {BRAND.license} ·{" "}
              <a href={GITHUB_URL} className="underline underline-offset-4">
                Source on GitHub
              </a>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
