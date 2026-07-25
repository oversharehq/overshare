export interface PlatformPage {
  slug: string;
  name: string;
  /** Used in <title> and the h1. */
  headline: string;
  metaDescription: string;
  intro: string[];
  /** What tends to actually turn up on apps from this platform. */
  commonFindings: { title: string; body: string }[];
  placeholder: string;
}

export const PLATFORMS: PlatformPage[] = [
  {
    slug: "lovable",
    name: "Lovable",
    headline: "Security scan for Lovable apps",
    metaDescription:
      "Free security scan for apps built with Lovable. Checks for exposed Supabase keys, leaked source maps, missing security headers and Row Level Security risk.",
    intro: [
      "Lovable generates both your frontend and your Supabase schema, which is what makes it fast and also what makes the access-control gap easy to miss. The generator will happily create tables and wire up queries without ever configuring who is allowed to read which rows.",
      "That gap became a documented one: CVE-2025-48757 covers Row Level Security misconfiguration in Lovable-built apps, where a survey of published projects found a meaningful share allowing unauthenticated reads of arbitrary tables. If you have not explicitly written RLS policies, assume you do not have them.",
    ],
    commonFindings: [
      {
        title: "Supabase keys in the client bundle",
        body: "The anon key is meant to be public. The service_role key is not — it bypasses Row Level Security completely, and if it reached your frontend it is readable by anyone who opens developer tools.",
      },
      {
        title: "Row Level Security never configured",
        body: "Enabling RLS with no policy denies everything; adding a policy of USING (true) protects nothing. Both look equally 'done' from the dashboard.",
      },
      {
        title: "Source maps left on",
        body: "Default build settings often publish .map files, which reconstruct your original source alongside the minified bundle.",
      },
    ],
    placeholder: "https://myapp.lovable.app",
  },
  {
    slug: "bolt",
    name: "Bolt",
    headline: "Security scan for Bolt.new apps",
    metaDescription:
      "Free security scan for apps built with Bolt.new. Finds exposed API keys, source maps, CORS problems and missing security headers on your deployed app.",
    intro: [
      "Bolt.new builds and previews your app inside a browser-based WebContainer, then deploys it out to a normal host. There is no built-in security scan in that pipeline, so whatever the generator wrote is what ships.",
      "Because Bolt projects frequently wire up a backend through environment variables that get inlined at build time, the most common problem is a key that was only ever meant for server-side use ending up in the JavaScript bundle.",
    ],
    commonFindings: [
      {
        title: "Build-time environment variables in the bundle",
        body: "Any variable exposed to the client build gets baked into the shipped JavaScript. A secret key added this way is public the moment you deploy.",
      },
      {
        title: "Missing security headers",
        body: "Static hosts serve nothing by default. No CSP, no HSTS, no nosniff unless you configure them.",
      },
      {
        title: "Permissive CORS",
        body: "Backends generated for local development often accept any origin, and that configuration follows the app into production.",
      },
    ],
    placeholder: "https://myapp.netlify.app",
  },
  {
    slug: "v0",
    name: "v0",
    headline: "Security scan for v0 apps",
    metaDescription:
      "Free security scan for apps built with v0 by Vercel. Checks bundles for exposed keys, plus headers, TLS, CORS and DNS configuration.",
    intro: [
      "v0 generates Next.js applications, which means the client and server boundary is real but easy to cross by accident. A value read in a Client Component is a value shipped to the browser, regardless of what you named it.",
      "The most common issue on generated Next.js apps is a secret referenced from a component that turned out to be client-side, or one prefixed NEXT_PUBLIC_ because that was what made the build stop complaining.",
    ],
    commonFindings: [
      {
        title: "NEXT_PUBLIC_ prefixed secrets",
        body: "The prefix does exactly what it says. Anything carrying it is compiled into the client bundle and served to every visitor.",
      },
      {
        title: "Server-only keys in Client Components",
        body: "Adding 'use client' to a component that reads a secret quietly moves that secret into the browser bundle.",
      },
      {
        title: "Database keys from generated integrations",
        body: "Generated Supabase or Postgres wiring sometimes reaches for the privileged key because it is the one that always works.",
      },
    ],
    placeholder: "https://myapp.vercel.app",
  },
  {
    slug: "replit",
    name: "Replit",
    headline: "Security scan for Replit apps",
    metaDescription:
      "Free security scan for apps built and hosted on Replit. Finds exposed keys in client bundles, missing headers, TLS problems and forgotten subdomains.",
    intro: [
      "Replit collapses editing, running and hosting into one place, which is convenient and also means a project that started as an experiment can end up publicly reachable without anyone deciding it should be.",
      "Apps deployed from Replit are frequently still serving development configuration: verbose errors, permissive CORS, and secrets that were pasted inline while getting something working.",
    ],
    commonFindings: [
      {
        title: "Development configuration in production",
        body: "Debug output and permissive CORS settings that were fine on localhost are still in place on the public URL.",
      },
      {
        title: "Hardcoded keys",
        body: "Keys pasted directly into source while iterating, rather than read from Replit Secrets, end up in the served bundle.",
      },
      {
        title: "Forgotten deployments",
        body: "Old versions of a project can remain publicly reachable long after you have moved on from them.",
      },
    ],
    placeholder: "https://myapp.replit.app",
  },
  {
    slug: "base44",
    name: "Base44",
    headline: "Security scan for Base44 apps",
    metaDescription:
      "Free security scan for apps built with Base44. Checks the public surface for exposed credentials, source maps, headers and CORS configuration.",
    intro: [
      "Base44 generates full-stack applications with the data layer wired up for you. As with every generator in this category, the code that gets written is only as locked down as the access rules you configure afterwards.",
      "A passive scan tells you what the generated app is currently handing to anyone who visits it, which is the fastest way to find out whether the defaults were safe.",
    ],
    commonFindings: [
      {
        title: "Credentials in the shipped bundle",
        body: "Generated data-layer wiring can reach for a privileged key rather than a scoped one.",
      },
      {
        title: "Missing security headers",
        body: "CSP, HSTS and nosniff are rarely configured by default on generated deployments.",
      },
      {
        title: "Source maps published alongside the build",
        body: "Default production builds often ship maps, which undo minification entirely.",
      },
    ],
    placeholder: "https://myapp.base44.app",
  },
  {
    slug: "cursor",
    name: "Cursor",
    headline: "Security scan for apps built with Cursor",
    metaDescription:
      "Free security scan for web apps written with Cursor. Checks your deployed app for exposed keys, source maps, headers, TLS and CORS configuration.",
    intro: [
      "Cursor is an editor rather than a host, so there is no single deployment shape to check. What the scan looks at is wherever your app actually ended up — Vercel, Netlify, Fly, your own server.",
      "The pattern worth knowing about is not specific to Cursor but is well documented for AI-assisted development generally: a Stanford study found developers using AI assistants produced vulnerable code on security-sensitive tasks noticeably more often, while rating their own code as more secure than it was. Confidence is the risk, not the tooling.",
    ],
    commonFindings: [
      {
        title: "Secrets that moved client-side during a refactor",
        body: "A value that was server-only can end up in the browser bundle when a component is restructured, with nothing flagging the move.",
      },
      {
        title: "Generated auth and access rules that were never tightened",
        body: "Permissive defaults written to get a feature working tend to survive to production unless something checks them.",
      },
      {
        title: "Missing transport configuration",
        body: "Headers, TLS settings and CORS rules are rarely part of what gets generated.",
      },
    ],
    placeholder: "https://myapp.com",
  },
];

export function findPlatform(slug: string): PlatformPage | undefined {
  return PLATFORMS.find((platform) => platform.slug === slug);
}
