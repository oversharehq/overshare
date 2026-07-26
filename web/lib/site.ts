export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

// Opt-in rather than opt-out: a deploy that forgets the flag stays out of the
// index. Indexing is close to irreversible — a page crawled before the
// false-positive rate is measured keeps ranking for a claim METHODOLOGY.md
// explicitly says is unmeasured, and the `todo` markers ship with it.
export const INDEXABLE = process.env.NEXT_PUBLIC_INDEXABLE === "true";
