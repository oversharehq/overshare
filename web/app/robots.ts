import type { MetadataRoute } from "next";
import { INDEXABLE, SITE_URL } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  // Crawling stays allowed while unindexed, deliberately. Blocking it here
  // would stop crawlers reading the noindex in the page metadata, and a
  // disallowed URL can still be indexed URL-only if something links to it.
  // Allow the crawl, let the noindex do the work, advertise no sitemap.
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Reports may describe apps the submitter does not own.
      disallow: ["/scan/", "/api/"],
    },
    ...(INDEXABLE ? { sitemap: `${SITE_URL}/sitemap.xml` } : {}),
  };
}
