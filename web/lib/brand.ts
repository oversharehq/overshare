/**
 * Single source of truth for the product name.
 *
 * marketing/01-naming.md argues against "LeakScan" and was overruled — the name
 * stays. Its §5 condition still applies: because "leak" is fear-register and the
 * positioning is proof, the copy has to carry the trust framing that the name
 * does not, and has to work harder to communicate that this runs continuously.
 *
 * Everything below is one find-replace if that decision is revisited.
 */
export const BRAND = {
  name: "LeakScan",
  /** CLI command and PyPI package. Matches [project.scripts] in pyproject.toml. */
  cmd: "leakscan",
  license: "Apache-2.0",
} as const;

/**
 * TODO(pre-launch): the repo is not published yet, so this 404s. Every "View on
 * GitHub" CTA depends on it, and marketing/01-naming.md §4 lists the GitHub org
 * as an unverified availability check.
 */
export const GITHUB_URL = "https://github.com/leakscan/leakscan";
