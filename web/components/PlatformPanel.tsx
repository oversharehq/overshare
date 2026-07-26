import type { Platform } from "@/lib/types";
import { Block } from "./Paper";

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
    <Block index="02" title="Detected stack">
      <p className="max-w-[34rem] text-[0.95rem] leading-[1.6] text-ink-soft">
        Fingerprinted from what the app serves publicly. This determines which
        checks are relevant.
      </p>

      <dl className="mt-5 grid grid-cols-2 border-t border-rule sm:grid-cols-4">
        {entries.map(([key, value]) => (
          <div
            key={key}
            className="border-b border-rule py-3 sm:border-b-0 sm:border-r sm:px-3 sm:last:border-r-0 sm:first:pl-0"
          >
            <dt className="label text-faint">{LABELS[key]}</dt>
            <dd className="mt-1.5 font-mono text-sm text-ink">{value}</dd>
          </div>
        ))}
      </dl>

      {platform.api_url && (
        <p className="mt-4 break-all font-mono text-xs text-mute">
          {platform.api_url}
        </p>
      )}
    </Block>
  );
}
