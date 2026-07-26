/**
 * Single source of truth for the product name.
 *
 * Named Overshare because it describes the actual finding: a published source
 * map or a missing CSP is not a *leak*, but it is oversharing. See
 * marketing/01-naming.md — the previous name was dropped over a verified
 * same-category collision, not taste.
 */
export const BRAND = {
  name: "Overshare",
  /** CLI command and PyPI package. Matches [project.scripts] in pyproject.toml. */
  cmd: "overshare",
  domain: "oversharehq.com",
  license: "Apache-2.0",
} as const;

/**
 * The GitHub *org* is `oversharehq`, not `overshare` — github.com/overshare is
 * already taken. marketing/01-naming.md §5.
 */
export const GITHUB_URL = "https://github.com/oversharehq/overshare";
