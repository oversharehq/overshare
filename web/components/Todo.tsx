/**
 * Visible marker for copy that depends on something that does not exist yet.
 *
 * Deliberately loud. marketing/04-landing-page.md forbids placeholder statistics
 * and fake trust signals, so the rule here is that the surrounding sentence must
 * still be true with this marker removed — the marker flags a missing artifact,
 * it never stands in for an unmeasured number.
 */
export function Todo({ children }: { children: React.ReactNode }) {
  return (
    <span className="my-1 inline-flex items-baseline gap-2 border-l-2 border-flag bg-flag-wash px-2.5 py-1.5 align-middle font-mono text-xs leading-[1.6] text-flag">
      <span className="label shrink-0 font-semibold">todo</span>
      <span>{children}</span>
    </span>
  );
}
