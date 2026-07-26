import type { MetadataRoute } from "next";
import { PLATFORMS } from "@/lib/platforms";
import { INDEXABLE, SITE_URL as siteUrl } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  if (!INDEXABLE) return [];

  return [
    { url: siteUrl, changeFrequency: "weekly", priority: 1 },
    {
      url: `${siteUrl}/methodology`,
      changeFrequency: "monthly" as const,
      priority: 0.9,
    },
    {
      url: `${siteUrl}/acceptable-use`,
      changeFrequency: "yearly" as const,
      priority: 0.4,
    },
    ...PLATFORMS.map((platform) => ({
      url: `${siteUrl}/p/${platform.slug}`,
      changeFrequency: "monthly" as const,
      priority: 0.8,
    })),
  ];
}
