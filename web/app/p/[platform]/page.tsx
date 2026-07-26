import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CommandBlock } from "@/components/CommandBlock";
import { ScanForm } from "@/components/ScanForm";
import { BRAND } from "@/lib/brand";
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
      <article className="py-14 sm:py-16">
        <p className="label text-flag">{platform.name}</p>
        <h1 className="mt-4 text-[2.2rem] leading-[1.1] font-medium tracking-[-0.02em] text-balance sm:text-[2.8rem]">
          {platform.headline}
        </h1>

        <div className="mt-7 max-w-[36rem] space-y-4 text-[1.0625rem] leading-[1.65] text-ink-soft">
          {platform.intro.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </div>

        <div className="mt-10">
          <p className="label mb-3 text-faint">Scan your app</p>
          <ScanForm placeholder={platform.placeholder} />
        </div>

        <div className="mt-8">
          <p className="label mb-3 text-faint">Or run it yourself</p>
          <CommandBlock
            lines={[
              `pip install ${BRAND.cmd}`,
              `${BRAND.cmd} ${platform.placeholder} --fail-on high`,
            ]}
          />
        </div>

        <section className="mt-16 border-t border-rule pt-10">
          <h2 className="max-w-2xl text-[1.65rem] leading-[1.15] font-medium tracking-tight">
            What usually turns up on {platform.name} apps
          </h2>
          <div className="mt-7 max-w-[36rem] divide-y divide-rule border-t border-rule">
            {platform.commonFindings.map((finding, index) => (
              <div
                key={finding.title}
                className="py-5 sm:grid sm:grid-cols-[2.5rem_1fr]"
              >
                <p className="label pt-1.5 text-faint tabular-nums">
                  {String(index + 1).padStart(2, "0")}
                </p>
                <div>
                  <h3 className="text-[1.05rem] font-medium text-ink">
                    {finding.title}
                  </h3>
                  <p className="mt-1.5 text-[0.95rem] leading-[1.65] text-ink-soft">
                    {finding.body}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-14 border-l-2 border-rule-firm bg-inset px-5 py-5">
          <h2 className="label text-mute">What the scan actually does</h2>
          <p className="mt-2.5 max-w-[34rem] text-[0.95rem] leading-[1.65] text-ink">
            It fetches your app the way any visitor&apos;s browser would, reads
            the JavaScript it ships, and checks the headers, certificate and DNS
            records that go with it. No login is attempted, nothing is modified,
            and no credential is used that was not already public.
          </p>
          <Link
            href="/#checks"
            className="mt-4 inline-block font-mono text-xs text-ink underline decoration-rule-firm underline-offset-4 transition-colors hover:text-flag"
          >
            See the full check list →
          </Link>
        </section>

        <section className="mt-14 border-t border-rule pt-6">
          <h2 className="label text-faint">Other platforms</h2>
          <ul className="mt-3 flex flex-wrap gap-x-6 gap-y-2">
            {others.map((entry) => (
              <li key={entry.slug}>
                <Link
                  href={`/p/${entry.slug}`}
                  className="font-mono text-xs text-ink underline decoration-rule-firm underline-offset-4 transition-colors hover:text-flag"
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
