import type { MetadataRoute } from "next";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Reports may describe apps the submitter does not own.
      disallow: ["/scan/", "/api/"],
    },
    sitemap: `${siteUrl}/sitemap.xml`,
  };
}
