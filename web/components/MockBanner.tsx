/** Server component: LEAKSCAN_API_URL is never exposed to the client. */
export function MockBanner() {
  if (process.env.LEAKSCAN_API_URL) return null;

  return (
    <div className="print-hidden mb-6 rounded-md border border-violet-300 bg-violet-50 px-4 py-3 text-sm text-violet-900">
      <strong className="font-semibold">Sample data.</strong> No scanner backend is
      connected, so this report is a fixture used to build the interface. Set{" "}
      <code className="font-mono text-xs">LEAKSCAN_API_URL</code> to scan for real.
    </div>
  );
}
