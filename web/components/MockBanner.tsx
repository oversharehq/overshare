/** Server component: OVERSHARE_API_URL is never exposed to the client. */
export function MockBanner() {
  if (process.env.OVERSHARE_API_URL) return null;

  return (
    <div className="print-hidden mb-8 border-l-2 border-flag bg-flag-wash px-4 py-3">
      <p className="label text-flag">Sample data</p>
      <p className="mt-1.5 text-[0.95rem] leading-[1.6] text-flag">
        No scanner backend is connected, so this report is a fixture used to
        build the interface. Set{" "}
        <code className="font-mono text-[0.85em]">OVERSHARE_API_URL</code> to
        scan for real.
      </p>
    </div>
  );
}
