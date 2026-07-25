import type { MetadataRoute } from "next";
import { PLATFORMS } from "@/lib/platforms";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: siteUrl, changeFrequency: "weekly", priority: 1 },
    ...PLATFORMS.map((platform) => ({
      url: `${siteUrl}/p/${platform.slug}`,
      changeFrequency: "monthly" as const,
      priority: 0.8,
    })),
  ];
}
