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
    <span className="my-1 inline-flex items-start gap-1.5 rounded border border-amber-400 bg-amber-50 px-2 py-1 align-middle text-xs font-medium text-amber-900">
      <span className="font-mono font-bold uppercase tracking-wide">todo</span>
      <span className="font-normal">{children}</span>
    </span>
  );
}
