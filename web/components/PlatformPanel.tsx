import type { Platform } from "@/lib/types";

const LABELS: Record<string, string> = {
  builder: "Built with",
  backend: "Backend",
  framework: "Framework",
  host: "Hosting",
};

const DISPLAY_ORDER = ["builder", "backend", "framework", "host"] as const;

export function PlatformPanel({ platform }: { platform: Platform }) {
  const entries = DISPLAY_ORDER.map((key) => [key, platform[key]] as const).filter(
    (entry): entry is readonly [(typeof DISPLAY_ORDER)[number], string] =>
      Boolean(entry[1]),
  );

  if (entries.length === 0) return null;

  return (
    <section className="mt-8 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-sm font-semibold text-slate-900">Detected stack</h2>
      <p className="mt-1 text-xs text-slate-500">
        Fingerprinted from what the app serves publicly. This determines which
        checks are relevant.
      </p>

      <dl className="mt-4 flex flex-wrap gap-x-8 gap-y-3">
        {entries.map(([key, value]) => (
          <div key={key}>
            <dt className="text-xs uppercase tracking-wide text-slate-500">
              {LABELS[key]}
            </dt>
            <dd className="mt-0.5 font-mono text-sm text-slate-900">{value}</dd>
          </div>
        ))}
      </dl>

      {platform.api_url && (
        <p className="mt-4 break-all border-t border-slate-100 pt-3 font-mono text-xs text-slate-600">
          {platform.api_url}
        </p>
      )}
    </section>
  );
}
