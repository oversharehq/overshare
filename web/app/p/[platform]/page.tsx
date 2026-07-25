import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ScanForm } from "@/components/ScanForm";
import { PLATFORMS, findPlatform } from "@/lib/platforms";

export function generateStaticParams() {
  return PLATFORMS.map((platform) => ({ platform: platform.slug }));
}

export const dynamicParams = false;

export async function generateMetadata(
  props: PageProps<"/p/[platform]">,
): Promise<Metadata> {
  const { platform: slug } = await props.params;
  const platform = findPlatform(slug);
  if (!platform) return {};

  return {
    title: platform.headline,
    description: platform.metaDescription,
    alternates: { canonical: `/p/${platform.slug}` },
    openGraph: {
      title: platform.headline,
      description: platform.metaDescription,
      url: `/p/${platform.slug}`,
    },
  };
}

export default async function PlatformPage(props: PageProps<"/p/[platform]">) {
  const { platform: slug } = await props.params;
  const platform = findPlatform(slug);
  if (!platform) notFound();

  const others = PLATFORMS.filter((entry) => entry.slug !== platform.slug);

  return (
    <div className="mx-auto max-w-3xl px-6">
      <article className="py-16">
        <p className="text-sm font-medium text-slate-500">{platform.name}</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900">
          {platform.headline}
        </h1>

        <div className="mt-6 space-y-4">
          {platform.intro.map((paragraph) => (
            <p key={paragraph} className="text-lg text-slate-600">
              {paragraph}
            </p>
          ))}
        </div>

        <div className="mt-8">
          <ScanForm placeholder={platform.placeholder} />
        </div>

        <section className="mt-16 border-t border-slate-200 pt-10">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            What usually turns up on {platform.name} apps
          </h2>
          <div className="mt-6 space-y-6">
            {platform.commonFindings.map((finding) => (
              <div key={finding.title}>
                <h3 className="text-base font-semibold text-slate-900">
                  {finding.title}
                </h3>
                <p className="mt-1 text-slate-600">{finding.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-12 rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="text-base font-semibold text-slate-900">
            What the scan actually does
          </h2>
          <p className="mt-2 text-slate-600">
            It fetches your app the way any visitor&apos;s browser would, reads the
            JavaScript it ships, and checks the headers, certificate and DNS
            records that go with it. No login is attempted, nothing is modified,
            and no credential is used that was not already public.
          </p>
          <Link
            href="/#checks"
            className="mt-4 inline-block text-sm font-medium text-slate-700 underline underline-offset-4 hover:text-slate-900"
          >
            See the full check list
          </Link>
        </section>

        <section className="mt-12 border-t border-slate-200 pt-8">
          <h2 className="text-sm font-semibold text-slate-900">Other platforms</h2>
          <ul className="mt-3 flex flex-wrap gap-x-6 gap-y-2">
            {others.map((entry) => (
              <li key={entry.slug}>
                <Link
                  href={`/p/${entry.slug}`}
                  className="text-sm text-slate-600 underline underline-offset-4 hover:text-slate-900"
                >
                  {entry.name}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </article>
    </div>
  );
}
